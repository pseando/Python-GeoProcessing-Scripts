#
#2345678901234567890123456789012345678901234567890123456789012345678901234567890
#        1         2         3         4         5         6         7         8
# -----------------------------------------------------------------------------

#                                 UtilityCrossings.py
#
# PURPOSE:
#
# Create three separate point layers that show where stormwater, sanitary sewer,
# and water pipes cross.  Layers containing stormwater and sanitary sewer pipes
# also calculates the vertical distance between the two pipes.  Result is found in
# the "VertDiff" field.
#
# 
# 1).  A file geodatabase is created on the local system(currently in
#      "C:\TEMP\Crossings"). The naming convention for the file geodatabase is
#      "Crossings<YYYYMMDD>" where "<YYYYMMDD>" is the four digit year (YYYY),
#      two digit month (MM), and two digit day (DD).  Under the General Settings
#      tabs for the Environment Settings, Output has Z Values and Output has M Values are
#      Disabled.
#
# 2).  The three pipe feature classes for water (wnWaterMain, wnForceMain, and 
#      wnGravity), three pipe feature classes for sewer (snForceMain, snGravity, 
#      and snLateralLine), and the swPipes layer for stormwater are copied to
#      this local geodatabase. 
#      
# 3).  A text field ("Type") is added to each of the layers and populated with
#      a text string identifying the utility and subtype (lateral, gravity,
#      force).
#
# 4).  The three sanitary sewer line layers are merged together (snLines) and 
#      unnecessary attribute fields are eliminated.  The three water line layers 
#      are merged together (wnPipes) and unnecessary attribute fields are eliminated.
#
# 5).  The X and Y coordinates of the start of each pipe segment is calculated for
#      snLines and swPipes.  Coordinates are in NAD83Feet and NAVD88
#
# 6).  Intersect the swPipes and snLines layers.  Add X,Y coordinates, calculate length of swPipe and
#      snLine for each point, and invert of each pipe at intersection based on
#      pipe length and slope of pipe segment.  Calculate vertical distance between
#      swPipe and snLine based on inverts at intersection and pipe diameters.
#
# 7).  Intersect the wnPipes and snLines layers.  Since water pipe layer does not include inverts, 
#      vertical distance between pipes can not be calculated.  
#
# 8).  Intersect the wnPipes and swPipes layers.  Since water pipe layer does not include inverts, 
#      vertical distance between pipes can not be calculated.
#
# 9).  Merge three point feature classes together.

#-----------------------------------------------------------------------------
#
# DEPENDENCIES:
#
# 1).  ArcMap 9.3 or higher.
#
# 2).  A database connection to the server where the data is stored.
#
# 
#
# -----------------------------------------------------------------------------
# INPUT(S):
#
# 1). Layers from the Sewer, StormWater, and Water feature datasets.
#
# 
# -----------------------------------------------------------------------------
# OUTPUT(S):
#
# 1). See Purpose above for Outputs.
#
# -----------------------------------------------------------------------------
# NOTES:
#
# 
#
# TODO ITEMS (in no particular order)
# 1).  
# 2).  
#
# -----------------------------------------------------------------------------
# INSTALLATION INSTRUCTIONS:
#
# THIS IS FROM THE BUILDPARCELS.PY SCRIPT.
#
# Here is what the command should look like when used with "Schedule Tasks":
#
# cmd /c D:\ASSESSOR\SCRIPTS\BuildParcels.py >> BuildParcels_LOG.txt 2>&1
#
# -----------------------------------------------------------------------------
# HISTORY:
#
# (20120620-doig): Initial coding complete
# (20120629-doig): Added text field to indicate whether storm pipe is over or under sewer pipe.
# Changed calculation for vertical separation field so that it displays absolute value
# (20120712-doig): Added code so that vertical separation not calculated if valid Z at intersection
# not available for both storm and sewer.
# (20121106-doig): Added code to combine three feature classes into one.  Had to add delete field
# geoprocessing step to eliminate duplicate fields creted during merge process.
# ==============================================================================
#

# Import system modules
import sys, string, os, arcgisscripting, time, shutil


# Create the Geoprocessor object
gp = arcgisscripting.create(9.3)

# Load required toolboxes...
#gp.AddToolbox("C:/Program Files/ArcGIS/ArcToolbox/Toolboxes/Conversion Tools.tbx")
#gp.AddToolbox("C:/Program Files/ArcGIS/ArcToolbox/Toolboxes/Data Management Tools.tbx")

today=time.strftime("%Y%m%d", time.localtime())

def LogMessage( message):
    print time.strftime ("%Y-%m-%dT%H:%M:%S ", time.localtime()) + message
    return

# Set workspace
gp.Workspace="C:/TEMP/Crossings/Crossings" + today + ".gdb"


# variables...
#BUILDDIR="C:/TEMP/BUILD" + today
#BuildGDB=BUILDDIR + "/BUILD.gdb"

CrossingsDIR = "C:/TEMP/Crossings"

def  MakeBuildDirectory():

    LogMessage(" MakeBuildDirectory..." )
    os.mkdir(CrossingsDIR)
    os.chdir(CrossingsDIR)
    LogMessage(" MakeBuildDirectory Complete.")
    return

# Process: Create File GDB...
def MakeGDB():
    LogMessage(" Geodatabase creation...")
    FileGDBName="Crossings" + today
    OutputLocation=CrossingsDIR
        
    gp.CreateFileGDB_management(OutputLocation, FileGDBName)
    LogMessage(" Geodatabase created")
    return

# Process: Download stormwater pipe files.  
def CopySWFC():  
    SDEFC = "Database Connections\\Connection to durham-gis.sde\\gis_data.A1.StormWater\\gis_data.A1.swPipes"
##    gp.Workspace="C:/TEMP/Crossings/Crossings" + today + ".gdb"
    
    LogMessage(" Copy stormwater pipes start...")
    tempEnvironment6 = gp.outputZFlag
    gp.outputZFlag = "Disabled"
    tempEnvironment11 = gp.outputMFlag
    gp.outputMFlag = "Disabled"
    gp.CopyFeatures_management(SDEFC, "swPipes")
    gp.outputZFlag = tempEnvironment6
    gp.outputMFlag = tempEnvironment11
    LogMessage(" Copy stormwater pipes complete.")
    
    return

# Process: Add SWUtility Type Field...
def AddCalcSWFields():
        
    LogMessage(" Add and populate swPipes field...")
    gp.AddField_management("swPipes", "SWFID", "TEXT", "", "", "20", "Stormwater FacID", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("swPipes", "SWFID", "[FACILITYID]", "", "")
    gp.AddField_management("swPipes", "UtilType", "TEXT", "", "", "20", "Utility Type", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("swPipes", "UtilType", "\"Storm\"", "", "")
    gp.AddField_management("swPipes", "SWDiam", "SHORT", "5", "", "", "Stormwater Diameter", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("swPipes", "SWDiam", "[DIAMETER]", "", "")
    gp.AddField_management("swPipes", "SWLength", "DOUBLE", "38", "", "", "Storm Pipe Length", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("swPipes", "SWLength", "[Shape_Length]", "", "")
    gp.AddField_management("swPipes", "SWUpinvert", "DOUBLE", "38", "", "", "Stormwater Upstream Invert", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("swPipes", "SWUpinvert", "[INVERTUS]", "", "")
    gp.AddField_management("swPipes", "SWDninvert", "DOUBLE", "38", "", "", "Stormwater Downstream Invert", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("swPipes", "SWDninvert", "[INVERTDS]", "", "")
    gp.AddField_management("swPipes", "SWMaterial", "TEXT", "", "", "30", "Stormwater Material", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("swPipes", "SWMaterial", "[MATERIAL]", "", "")
##    decided to calculate slope fields to eliminate one area of possible error and inconsistency 
##    gp.AddField_management("swPipes", "SWslope", "DOUBLE", "38", "", "", "Stormwater Slope(%)", "NULLABLE", "NON_REQUIRED", "")
##    gp.CalculateField_management("swPipes", "SWslope", "[PSLOPE]", "", "")
##    gp.AddField_management("swPipes", "SWslope", "DOUBLE", "38", "", "", "Stormwater Slope Calculated(%)", "NULLABLE", "NON_REQUIRED", "")
##    gp.CalculateField_management("swPipes", "SWslope", "(([SWUpinvert]-[SWDninvert])/[SWLength])*100", "", "")
    gp.DeleteField_management("swPipes", "LEGACYID;FACILITYID;LOCATION;INSTALLYEAR;DEPTHUS;DEPTHDS;HEIGHT;INVERTUS;INVERTDS;DIAMETER;\
        WIDTH;COMMENT;SRCATTDATE;SRCCOMMENT;CREATEDATE;MODIFYDATE;EDITEDBY;ENABLED;MATERIAL;FORM;STATUS;SRCAGENCY;SRCATT;SRCUSDEPTH;\
        SRCDSDEPTH;TYPE;PSLOPE;ADMINAREA;CONDDATE;USCOND;USCONTENTS;USOBS;DSCOND;DSCONTENTS;DSOBS;CONDCMT;PROJECT_ID;DATEBUILT;TEMP_ID")
    LogMessage(" Stormwater updated." )
    return

# Process: Download snGravity pipe files.  
def CopySGFC():  
    SDEFC = "Database Connections\\Connection to durham-gis.sde\\gis_data.A1.SewerSystem\\gis_data.A1.snGravityMain"
        
    LogMessage(" Copy snGravity Start...")
    tempEnvironment6 = gp.outputZFlag
    gp.outputZFlag = "Disabled"
    tempEnvironment11 = gp.outputMFlag
    gp.outputMFlag = "Disabled"
    gp.CopyFeatures_management(SDEFC, "snGravity")
    gp.outputZFlag = tempEnvironment6
    gp.outputMFlag = tempEnvironment11
    LogMessage(" Copy snGravity Complete.")
    
    return

# Process: Add snGravityUtility Type Field...
def AddCalcSGFields():
            
    LogMessage(" Add and populate snGravity field...")
    gp.AddField_management("snGravity", "UtilType", "TEXT", "", "", "20", "Utility Type", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("snGravity", "UtilType", "\"snGravity\"", "", "")
    gp.AddField_management("snGravity", "SnMaterial", "TEXT", "", "", "30", "Sewer Material", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("snGravity", "SnMaterial", "[MATERIAL]", "", "")
    LogMessage(" Delete fields...")
    gp.DeleteField_management("snGravity", "ENABLED;ADMINISTRATIVEAREA;INSTALLDATE;OPERATIONALAREA;LIFECYCLESTATUS;WORKORDERID;\
        FLOWMEASUREMENTID;WATERTYPE;MATERIAL;EXTERIORCOATING;JOINTTYPE1;JOINTTYPE2;LININGTYPE;PIPECLASS;ROUGHNESS;BARRELCOUNT;\
        CROSSSECTIONSHAPE;MEASUREMENT1;MEASUREMENT2;NOMINALDIAMETER;BATCH;OWNER;RECORDEDLENGTH;LEGACYID;ITEMDESCRIPTION;\
        CONVPHASE;FROMMH;TOMH;TEMPID;BADSPAN;EASEMENTNUMBER;CREATEDATE;MODIFYDATE;EDITEDBY;HPL;NOTES;RELINEDATE;TEMP_ID;CID;\
        LOCATION;INSTALLYEAR;DEPTHUS;DEPTHDS;HEIGHT;WIDTH;COMMENT;SRCATTDATE;SRCCOMMENT;FORM;SRCAGENCY;SRCATT;SRCUSDEPTH;\
        SRCDSDEPTH;TYPE;ADMINAREA;CONDDATE;USCOND;USCONTENTS;USOBS;DSCOND;DSCONTENTS;DSOBS;CONDCMT;PROJECT_ID;DATEBUILT")
    LogMessage(" snGravity updated." )

    return

# Process: Download snLateral pipe files.  
def CopySLFC():  
    SDEFC = "Database Connections\\Connection to durham-gis.sde\\gis_data.A1.SewerSystem\\gis_data.A1.snLateralLine"
        
    LogMessage(" Copy snLateral Start...")
    tempEnvironment6 = gp.outputZFlag
    gp.outputZFlag = "Disabled"
    tempEnvironment11 = gp.outputMFlag
    gp.outputMFlag = "Disabled"
    gp.CopyFeatures_management(SDEFC, "snLateral")
    gp.outputZFlag = tempEnvironment6
    gp.outputMFlag = tempEnvironment11
    LogMessage(" Copy snLateral Complete.")
    
    return

# Process: Add snLateralUtility Type Field...
def AddCalcSLFields():
        
    LogMessage(" Add and populate snLateral field...")
    gp.AddField_management("snLateral", "UtilType", "TEXT", "", "", "20", "Utility Type", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("snLateral", "UtilType", "\"snLateral\"", "", "")
    gp.AddField_management("snLateral", "SnMaterial", "TEXT", "", "", "30", "Sewer Material", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("snLateral", "SnMaterial", "[MATERIAL]", "", "")
    LogMessage(" Delete fields...")
    gp.DeleteField_management("snLateral", "ENABLED;ADMINISTRATIVEAREA;INSTALLDATE;OPERATIONALAREA;LIFECYCLESTATUS;WORKORDERID;\
        FLOWMEASUREMENTID;WATERTYPE;MATERIAL;LOCATIONDESCRIPTION;BATCH;RECORDEDLENGTH;OWNER;ITEMDESCRIPTION;STATIONING;LEGACYID;\
        CONVPHASE;EASEMENTNUMBER;CREATEDATE;MODIFYDATE;EDITEDBY;TEMP_ID")
    LogMessage(" snLateral updated.")
    
    return

# Process: Download snForce pipe files.  
def CopySFFC():  
    SDEFC = "Database Connections\\Connection to durham-gis.sde\\gis_data.A1.SewerSystem\\gis_data.A1.snForceMain"
    
    LogMessage(" Copy snForce Start...")
    tempEnvironment6 = gp.outputZFlag
    gp.outputZFlag = "Disabled"
    tempEnvironment11 = gp.outputMFlag
    gp.outputMFlag = "Disabled"
    gp.CopyFeatures_management(SDEFC, "snForce")
    gp.outputZFlag = tempEnvironment6
    gp.outputMFlag = tempEnvironment11
    LogMessage(" Copy snForce Complete.")
    
    return

# Process: Add snForceUtility Type Field...
def AddCalcSFFields():

    LogMessage(" Add and populate snForce field...")
    gp.AddField_management("snForce", "UtilType", "TEXT", "", "", "20", "Utility Type", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("snForce", "UtilType", "\"snForce\"", "", "")
    gp.AddField_management("snForce", "SnMaterial", "TEXT", "", "", "30", "Sewer Material", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("snForce", "SnMaterial", "[MATERIAL]", "", "")
    LogMessage(" Delete fields...")
    gp.DeleteField_management("snForce", "ENABLED;ADMINISTRATIVEAREA;INSTALLDATE;OPERATIONALAREA;LIFECYCLESTATUS;WORKORDERID;\
        FLOWMEASUREMENTID;WATERTYPE;MATERIAL;EXTERIORCOATING;JOINTTYPE1;JOINTTYPE2;LININGTYPE;PIPECLASS;ROUGHNESS;DEPTH;\
        GROUNDSURFACETYPE;PRESSURERATING;BATCH;ITEMDESCRIPTION;CONNECTED;OWNER;LEGACYID;CONVPHASE;EASEMENTNUMBER;CREATEDATE;\
        MODIFYDATE;EDITEDBY;HPL;TEMP_ID;CID")
    LogMessage(" snForce updated.")
    
    return


# Process: Merge SS Pipes...
def MergesnFC():
        
    LogMessage(" Merge sewer pipes...")
    tempEnvironment6 = gp.outputZFlag
    gp.outputZFlag = "Disabled"
    tempEnvironment11 = gp.outputMFlag
    gp.outputMFlag = "Disabled"
    gp.Merge_management("snGravity; snLateral; snForce", "snPipes", "")
    gp.outputZFlag = tempEnvironment6
    gp.outputMFlag = tempEnvironment11
    LogMessage(" Sewer lines merged." )

    return


# Process: Clean up sewer pipe attribute fields...
def CleanupsnFC():
        
    LogMessage(" Clean up sewer pipe attribute fields...")
    gp.AddField_management("snPipes", "SnFID", "TEXT", "", "", "20", "Sewer FacID", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("snPipes", "SnFID", "[FACILITYID]", "", "")
    gp.AddField_management("snPipes", "SnDiam", "SHORT", "5", "", "", "Sewer Diameter", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("snPipes", "SnDiam", "[DIAMETER]", "", "")
    gp.AddField_management("snPipes", "SnLength", "DOUBLE", "38", "", "", "Sewer Pipe Length", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("snPipes", "SnLength", "[Shape_Length]", "", "")
    gp.AddField_management("snPipes", "SnUpinvert", "DOUBLE", "38", "", "", "Sewer Upstream Invert", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("snPipes", "SnUpinvert", "[UPSTREAMINVERT]", "", "")
    gp.AddField_management("snPipes", "SnDninvert", "DOUBLE", "38", "", "", "Sewer Downstream Invert", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("snPipes", "SnDninvert", "[DOWNSTREAMINVERT]", "", "")
##    decided to calculate slope fields to eliminate one area of possible error and inconsistency 
##    gp.AddField_management("SnPipes", "Snslope", "DOUBLE", "38", "", "", "Sewer Slope(%)", "NULLABLE", "NON_REQUIRED", "")
##    gp.CalculateField_management("snPipes", "Snslope", "[SLOPE]", "", "")
##    gp.AddField_management("SnPipes", "Snslope", "DOUBLE", "38", "", "", "Sewer Slope Calculated(%)", "NULLABLE", "NON_REQUIRED", "")
##    gp.CalculateField_management("snPipes", "Snslope", "(([SnUpinvert]-[SnDninvert])/[SnLength])*100", "", "")
    gp.DeleteField_management("snPipes","FACILITYID;UPSTREAMINVERT;DOWNSTREAMINVERT;SLOPE;DIAMETER")
    LogMessage(" Sewer attribute fields updated." )

    return

# Process: Calculate X,Y for swPipes
def CalcSWXY():

    LogMessage(" Calculate SW X,Y...")
    gp.AddField_management("swPipes", "SWUpX", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    gp.AddField_management("swPipes", "SWUpY", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    rows = gp.UpdateCursor("swPipes")
    row = rows.Next()
    
    while row:
        feature = row.shape
        row.SWUpX = feature.FirstPoint.X
        row.SWUpY = feature.FirstPoint.Y
        rows.UpdateRow(row)
        row = rows.Next()

    del row
    del rows

    LogMessage(" Calculate X,Y for swPipes complete.")
    
    return

# Process: Calculate X,Y for snPipes
def CalcSSXY():
    
    LogMessage(" Calculate SS X,Y...")
    gp.AddField_management("snPipes", "SSUpX", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    gp.AddField_management("snPipes", "SSUpY", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    rows = gp.UpdateCursor("snPipes")
    row = rows.Next()
    
    while row:
        feature = row.shape
        row.SSUpX = feature.FirstPoint.X
        row.SSUpY = feature.FirstPoint.Y
        rows.UpdateRow(row)
        row = rows.Next()

    del row
    del rows

    LogMessage(" Calculate X,Y for SSPipes complete.")
    
    return


# Process: Download wnGravity pipe files.  
def CopyWGFC():  
    SDEFC = "Database Connections\\Connection to durham-gis.sde\\gis_data.A1.WaterSystem\\gis_data.A1.wnGravityMain"
    
    LogMessage(" Copy wnGravity start...")
    tempEnvironment6 = gp.outputZFlag
    gp.outputZFlag = "Disabled"
    tempEnvironment11 = gp.outputMFlag
    gp.outputMFlag = "Disabled"
    gp.CopyFeatures_management(SDEFC, "wnGravity")
    gp.outputZFlag = tempEnvironment6
    gp.outputMFlag = tempEnvironment11
    LogMessage(" Copy wnGravity complete.")
    
    return

# Process: Add wnGravity Utility Type Field...
def AddCalcWGFields():
        
    LogMessage(" Add and populate wnGravity field...")
    gp.AddField_management("wnGravity", "UtilType", "TEXT", "", "", "20", "Utility Type", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("wnGravity", "UtilType", "\"wnGravity\"", "", "")
    gp.AddField_management("wnGravity", "WnMaterial", "TEXT", "", "", "30", "Water Material", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("wnGravity", "WnMaterial", "[MATERIAL]", "", "")
    LogMessage(" Delete fields...")
    gp.DeleteField_management("wnGravity", "ENABLED;ADMINISTRATIVEAREA;INSTALLDATE;OPERATIONALAREA;LIFECYCLESTATUS;WORKORDERID;\
        FLOWMEASUREMENTID;WATERTYPE;MATERIAL;EXTERIORCOATING;JOINTTYPE1;JOINTTYPE2;LININGTYPE;PIPECLASS;ROUGHNESS;BARRELCOUNT;\
        CROSSSECTIONSHAPE;MEASUREMENT1;MEASUREMENT2;NOMINALDIAMETER;BATCH;CONNECTED;OWNER;ITEMDESCRIPTION;CREATEDATE;MODIFYDATE;\
        EDITEDBY;TEMP_ID")
    LogMessage(" wnGravity updated." )

    return

# Process: Download wnLateral pipe files.  
def CopyWLFC():  
    SDEFC = "Database Connections\\Connection to durham-gis.sde\\gis_data.A1.WaterSystem\\gis_data.A1.wnLateralLine"
    
    LogMessage(" Copy wnLateral start...")
    tempEnvironment6 = gp.outputZFlag
    gp.outputZFlag = "Disabled"
    tempEnvironment11 = gp.outputMFlag
    gp.outputMFlag = "Disabled"
    gp.CopyFeatures_management(SDEFC, "wnLateral")
    gp.outputZFlag = tempEnvironment6
    gp.outputMFlag = tempEnvironment11
    LogMessage(" Copy wnLateral complete.")
    
    return

# Process: Add wnLateral Utility Type Field...
def AddCalcWLFields():
    
    LogMessage(" Add and populate wnLateral field...")
    gp.AddField_management("wnLateral", "UtilType", "TEXT", "", "", "20", "Utility Type", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("wnLateral", "UtilType", "\"wnLateral\"", "", "")
    gp.AddField_management("wnLateral", "WnMaterial", "TEXT", "", "", "30", "Water Material", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("wnLateral", "WnMaterial", "[MATERIAL]", "", "")
    LogMessage(" Delete fields...")
    gp.DeleteField_management("wnLateral","ENABLED;ADMINISTRATIVEAREA;INSTALLDATE;OPERATIONALAREA;LIFECYCLESTATUS;WORKORDERID;\
        FLOWMEASUREMENTID;WATERTYPE;MATERIAL;LOCATIONDESCRIPTION;BATCH;CONNECTED;OWNER;ITEMDESCRIPTION;LEGACYID;CONVPHASE;\
        EASEMENTNUMBER;CREATEDATE;MODIFYDATE;EDITEDBY;TEMP_ID")
    LogMessage(" wnLateral updated." )
    
    return

# Process: Download wnWaterMain pipe files.  
def CopyWMFC():  
    SDEFC = "Database Connections\\Connection to durham-gis.sde\\gis_data.A1.WaterSystem\\gis_data.A1.wnWaterMain"

    LogMessage(" Copy wnWaterMain start...")
    tempEnvironment6 = gp.outputZFlag
    gp.outputZFlag = "Disabled"
    tempEnvironment11 = gp.outputMFlag
    gp.outputMFlag = "Disabled"
    gp.CopyFeatures_management(SDEFC, "wnWaterMain")
    gp.outputZFlag = tempEnvironment6
    gp.outputMFlag = tempEnvironment11
    LogMessage(" Copy wnWaterMain complete.")
    
    return

# Process: Add wnWaterMain Utility Type Field...
def AddCalcWMFields():
    
    LogMessage(" Add and populate field...")
    gp.AddField_management("wnWaterMain", "UtilType", "TEXT", "", "", "20", "Utility Type", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("wnWaterMain", "UtilType", "\"wnMain\"", "", "")
    gp.AddField_management("wnWaterMain", "WnMaterial", "TEXT", "", "", "30", "Water Material", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("wnWaterMain", "WnMaterial", "[MATERIAL]", "", "")
    LogMessage(" Delete fields...")
    gp.DeleteField_management("wnWaterMain","ENABLED;ADMINISTRATIVEAREA;INSTALLDATE;OPERATIONALAREA;LIFECYCLESTATUS;WORKORDERID;\
        FLOWMEASUREMENTID;WATERTYPE;MATERIAL;EXTERIORCOATING;JOINTTYPE1;JOINTTYPE2;LININGTYPE;PIPECLASS;ROUGHNESS;DEPTH;\
        GROUNDSURFACETYPE;PRESSURERATING;BATCH;CONNECTED;OWNER;ITEMDESCRIPTION;LEGACYID;CONVPHASE;EASEMENTNUMBER;CREATEDATE;\
        MODIFYDATE;EDITEDBY;TEMP_ID;CID")
    LogMessage( " wnWaterMain updated." )
    
    return


# Process: Merge...
def MergewnFC():
    
    LogMessage(" Merge water pipes...")
    tempEnvironment6 = gp.outputZFlag
    gp.outputZFlag = "Disabled"
    tempEnvironment11 = gp.outputMFlag
    gp.outputMFlag = "Disabled"
    gp.Merge_management("wnGravity; wnLateral; wnWaterMain", "wnPipes", "")
    gp.outputZFlag = tempEnvironment6
    gp.outputMFlag = tempEnvironment11
    LogMessage(" Water lines merged.")

    return

# Process: Clean up water pipe attribute fields...
def CleanupwnFC():
        
    LogMessage(" Clean up water pipe attribute fields...")
    gp.AddField_management("wnPipes", "WnDiam", "SHORT", "5", "", "", "Water Diameter", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("wnPipes", "WnDiam", "[DIAMETER]", "", "")
    gp.AddField_management("wnPipes", "WnUpinvert", "DOUBLE", "38", "", "", "Water Upstream Invert", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("wnPipes", "WnUpinvert", "[UPSTREAMINVERT]", "", "")
    gp.AddField_management("wnPipes", "WnDninvert", "DOUBLE", "38", "", "", "Water Downstream Invert", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("wnPipes", "WnDninvert", "[DOWNSTREAMINVERT]", "", "")
    gp.AddField_management("wnPipes", "Wnslope", "DOUBLE", "38", "", "", "Water Slope(%)", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("wnPipes", "Wnslope", "[SLOPE]", "", "")
    gp.AddField_management("wnPipes", "WnFID", "TEXT", "", "", "20", "Water FacID", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("wnPipes", "WnFID", "[FACILITYID]", "", "")
    gp.DeleteField_management("wnPipes","FACILITYID;UPSTREAMINVERT;DOWNSTREAMINVERT;SLOPE;DIAMETER")
    LogMessage(" Water attribute fields updated." )

    return


# Process: Intersect SWSS...
def IntersectSWSS():
#    gp.Workspace="C:/TEMP/Crossings/Crossings" + today + ".gdb"
    
    LogMessage(" Intersect sewer and storm pipes...")
    tempEnvironment10 = gp.outputZFlag
    gp.outputZFlag = "Disabled"
    tempEnvironment17 = gp.outputMFlag
    gp.outputMFlag = "Disabled"
    gp.Intersect_analysis("snPipes; swPipes", "SWSSIntersect", "ALL", "", "POINT")
    gp.outputZFlag = tempEnvironment10
    gp.outputMFlag = tempEnvironment17
    LogMessage(" Intersect SWSS complete")

    return

# Process: Add Intersection Type field and populate...
def SWSSIntersectType():
    gp.AddField_management("SWSSIntersect", "InterType", "TEXT", "", "", "50", "Intersection Type", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("SWSSIntersect", "InterType", "\"Sewer-Storm\"", "", "")
    LogMessage(" Intersect type added")

    return

# Process: Intersect SWW...
def IntersectSWW():
        
    LogMessage(" Intersect water and storm pipes...")
    tempEnvironment10 = gp.outputZFlag
    gp.outputZFlag = "Disabled"
    tempEnvironment17 = gp.outputMFlag
    gp.outputMFlag = "Disabled"
    gp.Intersect_analysis("wnPipes; swPipes", "SWWIntersect", "ALL", "", "POINT")
    gp.outputZFlag = tempEnvironment10
    gp.outputMFlag = tempEnvironment17
    LogMessage(" Intersect SWW complete")

    return

# Process: Add Intersection Type field and populate...
def SWWIntersectType():
    gp.AddField_management("SWWIntersect", "InterType", "TEXT", "", "", "50", "Intersection Type", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("SWWIntersect", "InterType", "\"Water-Storm\"", "", "")
    LogMessage(" Intersect type added")

    return
# Process: Intersect SSW...
def IntersectSSW():
        
    LogMessage(" Intersect sewer and water pipes...")
    tempEnvironment10 = gp.outputZFlag
    gp.outputZFlag = "Disabled"
    tempEnvironment17 = gp.outputMFlag
    gp.outputMFlag = "Disabled"
    gp.Intersect_analysis("snPipes; wnPipes", "SSWIntersect", "ALL", "", "POINT")
    gp.outputZFlag = tempEnvironment10
    gp.outputMFlag = tempEnvironment17
    LogMessage(" Intersect SSW complete")

    return

# Process: Add Intersection Type field and populate...
def SSWIntersectType():
    gp.AddField_management("SSWIntersect", "InterType", "TEXT", "", "", "50", "Intersection Type", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("SSWIntersect", "InterType", "\"Sewer-Water\"", "", "")
    LogMessage(" Intersect type added")

    return

# Process: Calculate vertical difference for SSSW intersect point file...
def SSSWVertSep():

##    gp.Workspace="C:/TEMP/Crossings/Crossings20120628.gdb"

    LogMessage(" Change zero values to NULL")

    gp.MakeFeatureLayer_management("SWSSIntersect", "SWSSIntersect_Layer3", "", "", "")

    gp.SelectLayerByAttribute("SWSSIntersect_Layer3", "NEW_SELECTION", "SnUpinvert=0")

    gp.CalculateField_management("SWSSIntersect_Layer3", "SnUpinvert", "NULL", "", "")

    gp.SelectLayerByAttribute("SWSSIntersect_Layer3", "NEW_SELECTION", "SnDninvert=0")

    gp.CalculateField_management("SWSSIntersect_Layer3", "SnDninvert", "NULL", "", "")

    gp.SelectLayerByAttribute("SWSSIntersect_Layer3", "NEW_SELECTION", "SWUpinvert=0 OR SWUpinvert=-9999")

    gp.CalculateField_management("SWSSIntersect_Layer3", "SWUpinvert", "NULL", "", "")

    gp.SelectLayerByAttribute("SWSSIntersect_Layer3", "NEW_SELECTION", "SWDninvert=0 OR SWDninvert=-9999")

    gp.CalculateField_management("SWSSIntersect_Layer3", "SWDninvert", "NULL", "", "")

    LogMessage(" Change -9999 values in stormwater pipe diameters to zero")

    gp.SelectLayerByAttribute("SWSSIntersect_Layer3", "NEW_SELECTION", "SWDiam=-9999")

    gp.CalculateField_management("SWSSIntersect_Layer3", "SWDiam", "0", "", "")
    

    LogMessage(" Calculate X,Y")

    LogMessage(" Calculating X,Y at SS-SW intersection")

    gp.AddXY_management("SWSSIntersect")

    LogMessage(" Make feature layer")

##    gp.MakeFeatureLayer_management("SWSSIntersect", "SWSSIntersect_Layer", "\"SnUpinvert\" > 0 AND \"SnDninvert\" > 0 AND \
##        \"SWUpinvert\" > 0 AND \"SWDninvert\" > 0", "", "")

    gp.MakeFeatureLayer_management("SWSSIntersect", "SWSSIntersect_Layer", "", "", "")

    LogMessage(" Calculating pipe slopes")
    gp.AddField_management("SWSSIntersect_Layer", "Snslope", "DOUBLE", "38", "", "", "Sewer Slope Calculated(%)", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("SWSSIntersect_Layer", "Snslope", "(([SnUpinvert]-[SnDninvert])/[SnLength])*100", "", "")
    gp.AddField_management("SWSSIntersect_Layer", "SWslope", "DOUBLE", "38", "", "", "Stormwater Slope Calculated(%)", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("SWSSIntersect_Layer", "SWslope", "(([SWUpinvert]-[SWDninvert])/[SWLength])*100", "", "")

    LogMessage(" Calculating pipe lengths for SS-SW intersection")

    gp.AddField_management("SWSSIntersect_Layer", "SS_Length", "DOUBLE", "", "", "", "Sewer Pipe Length", "NULLABLE", "NON_REQUIRED", "")
    gp.AddField_management("SWSSIntersect_Layer", "SW_Length", "DOUBLE", "", "", "", "Storm Pipe Length", "NULLABLE", "NON_REQUIRED", "")
    gp.CalculateField_management("SWSSIntersect_Layer", "SS_Length", "Sqr (( [SSUpX]- [POINT_X])^2+( [SSUpY]- [POINT_Y])^2  )", "", "")
    gp.CalculateField_management("SWSSIntersect_Layer", "SW_Length", "Sqr (( [SWUpX]- [POINT_X])^2+( [SWUpY]- [POINT_Y])^2  )", "", "")

    LogMessage(" Pipe lengths calculated for SS-SW intersections")

    gp.AddField_management("SWSSIntersect_Layer", "SS_Invert", "DOUBLE", "", "", "", "Sewer Invert", "NULLABLE", "NON_REQUIRED", "")
    gp.AddField_management("SWSSIntersect_Layer", "SW_Invert", "DOUBLE", "", "", "", "Storm Invert", "NULLABLE", "NON_REQUIRED", "")
    gp.AddField_management("SWSSIntersect_Layer", "CrossTy", "TEXT", "", "", "30", "Crossing Type", "NULLABLE", "NON_REQUIRED", "")
    gp.AddField_management("SWSSIntersect_Layer", "VertSep", "DOUBLE", "", "", "", "Vertical Separation", "NULLABLE", "NON_REQUIRED", "")
    gp.AddField_management("SWSSIntersect_Layer", "PipeInter", "TEXT", "", "", "20", "Do Pipes Intersect", "NULLABLE", "NON_REQUIRED", "")
    
    LogMessage(" Calculate inverts")

    gp.CalculateField_management("SWSSIntersect_Layer", "SS_Invert", "[SnUpinvert]-( [Snslope]/100* [SS_Length])", "", "")
    gp.CalculateField_management("SWSSIntersect_Layer", "SW_Invert", "[SWUpinvert]-( [SWslope]/100* [SW_Length])", "", "")

##    LogMessage(" Calculate vertical separation")
##
##    gp.CalculateField_management("SWSSIntersect_Layer", "VertSep", "[SW_Invert]- ([SS_Invert]+[SnDiam])", "", "")



##    LogMessage(" Calculate crossing type")
##
##    gp.SelectLayerByAttribute("SWSSIntersect_Layer", "NEW_SELECTION", "VertSep > 0 AND VertSep < 20")
##
##    gp.CalculateField_management("SWSSIntersect_Layer", "CrossTy", "\"storm over sewer\"", "", "")
##
##    gp.SelectLayerByAttribute("SWSSIntersect_Layer", "NEW_SELECTION", "VertSep < 0 AND VertSep > -20")
##
##    gp.CalculateField_management("SWSSIntersect_Layer", "CrossTy", "\"sewer over storm\"", "", "")
##
##    gp.SelectLayerByAttribute("SWSSIntersect_Layer", "NEW_SELECTION", "VertSep < -20 OR VertSep > 20")
##
##    gp.CalculateField_management("SWSSIntersect_Layer", "CrossTy", "\"bad data?\"", "", "")
##
##    gp.SelectLayerByAttribute("SWSSIntersect_Layer", "NEW_SELECTION", "SWUpX > 0")
##
##    gp.CalculateField_management("SWSSIntersect", "VertSep", "Abs ( [SW_Invert] - ([SS_Invert]+[SnDiam]))", "", "")
##  
##    LogMessage(" Calculation complete")
##
##    gp.MakeFeatureLayer_management("SWSSIntersect", "SWSSIntersect_Layer2", "\"CrossTy\" IS NULL", "", "")
##
##    gp.CalculateField_management("SWSSIntersect_Layer2", "CrossTy", "\"missing data\"", "", "")
##   
##    LogMessage(" Calculations complete.")

    
# Calculate vertical separation

    LogMessage(" Calculate vertical separation")

    gp.SelectLayerByAttribute("SWSSIntersect_Layer", "NEW_SELECTION", "SW_Invert > SS_Invert")

    gp.CalculateField_management("SWSSIntersect_Layer", "VertSep", "[SW_Invert]- ([SS_Invert]+([SnDiam]/12))", "", "")

    gp.SelectLayerByAttribute("SWSSIntersect_Layer", "NEW_SELECTION", "SS_Invert > SW_Invert")

    gp.CalculateField_management("SWSSIntersect_Layer", "VertSep", "[SS_Invert]- ([SW_Invert]+([SWDiam]/12))", "", "")

    LogMessage(" Vertical separation calculation complete")

# Calculate crossing type

    LogMessage(" Calculate crossing type")

    gp.SelectLayerByAttribute("SWSSIntersect_Layer", "NEW_SELECTION", "SW_Invert > SS_Invert")

    gp.CalculateField_management("SWSSIntersect_Layer", "CrossTy", "\"Storm over Sewer\"", "", "")

    gp.SelectLayerByAttribute("SWSSIntersect_Layer", "NEW_SELECTION", "SW_Invert < SS_Invert")

    gp.CalculateField_management("SWSSIntersect_Layer", "CrossTy", "\"Sewer over Storm\"", "", "")

    gp.SelectLayerByAttribute("SWSSIntersect_Layer", "NEW_SELECTION", "VertSep > 20")

    gp.CalculateField_management("SWSSIntersect_Layer", "CrossTy", "\"Bad Data?\"", "", "")

    LogMessage (" Crossing type calculation complete")
    
  # Calculate whether pipes intersect

    gp.SelectLayerByAttribute ("SWSSIntersect_Layer", "NEW_SELECTION", "VertSep < 0")

    gp.CalculateField_management("SWSSIntersect_Layer", "PipeInter", "\"Yes\"", "", "")

    gp.SelectLayerByAttribute ("SWSSIntersect_Layer", "NEW_SELECTION", "VertSep > 0")

    gp.CalculateField_management("SWSSIntersect_Layer", "PipeInter", "\"No\"", "", "")

##    gp.SelectLayerByAttribute("SWSSIntersect_Layer", "NEW_SELECTION", "SWUpX > 0")
##
##    gp.CalculateField_management("SWSSIntersect", "VertSep", "Abs ([VertSep])", "", "")
##  
   
    gp.MakeFeatureLayer_management("SWSSIntersect", "SWSSIntersect_Layer2", "\"CrossTy\" IS NULL", "", "")

    gp.SelectLayerByAttribute ("SWSSIntersect_Layer2", "NEW_SELECTION", "SS_Invert IS NULL AND SW_Invert IS NULL")

    gp.CalculateField_management("SWSSIntersect_Layer2", "CrossTy", "\"Sewer and Storm Missing\"", "", "")

    gp.SelectLayerByAttribute ("SWSSIntersect_Layer2", "NEW_SELECTION", "SS_Invert IS NULL AND SW_Invert IS NOT NULL")

    gp.CalculateField_management("SWSSIntersect_Layer2", "CrossTy", "\"Sewer Data Missing\"", "", "")

    gp.SelectLayerByAttribute ("SWSSIntersect_Layer2", "NEW_SELECTION", "SW_Invert IS NULL AND SS_Invert IS NOT NULL")

    gp.CalculateField_management("SWSSIntersect_Layer2", "CrossTy", "\"Storm Data Missing\"", "", "")

    return

    
# Process: Merge...
def Merge3Intersects():
    
    LogMessage(" Merge feature classes...")
    tempEnvironment6 = gp.outputZFlag
    gp.outputZFlag = "Disabled"
    tempEnvironment11 = gp.outputMFlag
    gp.outputMFlag = "Disabled"
    gp.Merge_management("SWWIntersect; SSWIntersect; SWSSIntersect", "AllIntersections", "")
    gp.outputZFlag = tempEnvironment6
    gp.outputMFlag = tempEnvironment11
    LogMessage(" Feature classes merged.")

    return

def FinalCleanup():

    LogMessage(" Delete duplicate fields.")
    gp.DeleteField_management("AllIntersections", "SUBTYPE;UtilType;FID_swPipes;UtilType_1;FID_wnPipes;SUBTYPE_1;FID_snPipes_1;\
        SUBTYPE_12;UtilType_12;SnFID_1;SnDiam_1;SnLength_1;SnUpinvert_1;SnDninvert_1;SSUpX_1;SSUpY_1;FID_swPipes_1;SWFID_1;\
        UtilType_12_13;SWDiam_1;SWLength_1;SWUpinvert_1;SWDninvert_1;SWUpX_1;SWUpY_1;InterType_1;POINT_X_1;POINT_Y_1;Snslope_1;\
        SWslope_1;SS_Length_1;SW_Length_1;SS_Invert_1;SW_Invert_1;CrossTy_1;VertSep_1;FID_wnPipes_1;SUBTYPE_12_13;WnDiam_1;\
        WnUpinvert_1;WnDninvert_1;Wnslope_1;WnFID_1;FID_snPipes_12;SUBTYPE_12_13_14;UtilType_12_13_14;SnFID_12;SnDiam_12;\
        SnLength_12;SnUpinvert_12;SnDninvert_12;SSUpX_12;SSUpY_12;FID_swPipes_12;SWFID_12;UtilType_12_13_14_15;SWDiam_12;\
        SWLength_12;SWUpinvert_12;SWDninvert_12;SWUpX_12;SWUpY_12;InterType_12;POINT_X_12;POINT_Y_12;Snslope_12;SWslope_12;\
        SS_Length_12;SW_Length_12;SS_Invert_12;SW_Invert_12;CrossTy_12;VertSep_12;FID_wnPipes_12;SUBTYPE_12_13_14_15;WnDiam_12;\
        WnUpinvert_12;WnDninvert_12;Wnslope_12;WnFID_12;FID_snPipes_12_13;SUBTYPE_12_13_14_15_16;UtilType_12_13_14_15_16;\
        SnFID_12_13;SnDiam_12_13;SnLength_12_13;SnUpinvert_12_13;SnDninvert_12_13;SSUpX_12_13;SSUpY_12_13;FID_swPipes_12_13;\
        SWFID_12_13;UtilType_12_13_14_15_16_17;SWDiam_12_13;SWLength_12_13;SWUpinvert_12_13;SWDninvert_12_13;SWUpX_12_13;SWUpY_12_13;\
        InterType_12_13;POINT_X_12_13;POINT_Y_12_13;Snslope_12_13;SWslope_12_13;SS_Length_12_13;SW_Length_12_13;SS_Invert_12_13;\
        SW_Invert_12_13;CrossTy_12_13;VertSep_12_13;FID_wnPipes_12_13;SUBTYPE_12_13_14_15_16_17;WnDiam_12_13;WnUpinvert_12_13;\
        WnDninvert_12_13;Wnslope_12_13;WnFID_12_13;WnMaterial_1;SWMaterial_1;SnMaterial_1;WnMaterial_12;SWMaterial_12;SnMaterial_12;\
        WnMaterial_12_13;SWMaterial_12_13;SnMaterial_12_13;PipeInter_1;PipeInter_12;PipeInter_12_13")
    LogMessage(" Duplicate fields deleted.")

    return


##  Alternate method for calculating crossing type.  Removed in favor of process above.
##    rows = gp.UpdateCursor("SWSSIntersect")
##    row = rows.Next()
##    
##    while row:
##        if row.VertSep > 0:
##            row.CrossTy = "storm over sewer"
##        elif row.VertSep < 0:
##            row.CrossTy = "sewer over storm"
##        else: 
##            row.CrossTy = "unknown"
##        print "hello"
##        rows.UpdateRow(row)
##        row = rows.next()
##
##    del row
##    del rows
##
##    gp.CalculateField_management("SWSSIntersect", "VertSep", "Abs ( [SW_Invert] - ([SS_Invert]+[SnDiam]))", "", "")
##    
##    LogMessage(" Vertical Separation complete")

# Call the functions
##MakeBuildDirectory()

##MakeGDB()

CopySWFC()

AddCalcSWFields()

CopySGFC()

AddCalcSGFields()

CopySLFC()

AddCalcSLFields()

CopySFFC()

AddCalcSFFields()

MergesnFC()

CleanupsnFC()

CalcSWXY()

CalcSSXY()

CopyWGFC()

AddCalcWGFields()

CopyWLFC()

AddCalcWLFields()

CopyWMFC()
    
AddCalcWMFields()

MergewnFC()

CleanupwnFC()

IntersectSWSS()

SWSSIntersectType()

IntersectSWW()

SWWIntersectType()

IntersectSSW()

SSWIntersectType()

SSSWVertSep()

Merge3Intersects()

FinalCleanup()

del gp





