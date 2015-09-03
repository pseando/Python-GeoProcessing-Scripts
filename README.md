# Python-GeoProcessing-Scripts
Script identifies the XY locations where utility infrastructure intersect and then, assuming that upstream and downstream
inverts are available, the Z value for each pipe is calculated at the intersection and the vertical difference between the pipes
is calculated.  An additional attribute indicates which pipe is above the other.  (In other words, for example, is the storm-
water pipe above or below the sanitary sewer pipe.)  Z values are never calculated for water intersections since water pipes
do not rely on gravity and slope is therefore not consistent along the pipe length.
