## GENERATE SPEED RANGE LOOKUP TABLE (EXCEL OUTPUT) FOR ENTIRE SYSTEM,
##  FROM SPEED RESTRICTION LINES, AND TRACKSEGMENT LINES TO ACCOUNT FOR TRACKS WITH NO SPEED RESTRICTION.
##  - ASSUME MAX PERMISSIBLE SPEED (PER SUBDIV) FOR ANY MAINS IN SUBDIV NOT COVERED BY SPEED RESTRICTION RECORD.
##  - ASSUME RESTRICTED SPEED OF 15 MPH FOR ANY OTHER TRACKS (NOT MAIN) IN SUBDIV NOT COVERED BY SPEED RESTRICTION RECORD.

# TO BE RUN FOR ONE TRAIN TYPE AT A TIME, FOR ENTIRE NS SYSTEM AT ONCE.

################################################################################

# notes:

# Speed Restrictions that will be excluded:
#  - restrictions with HEADENDFLAG = 'Y'
#  - restrictions with RESTRICTIONTYPE <> 'Generic'
#  - restrictions with DIRECTION <> 'Bidirectional'


################################################################################


# 1
# inputs/prep


import arcpy as a
from arcpy import env
import datetime


# define today's date (datesuffix) for output file naming
today = datetime.datetime.now()

year = str(today.year)
if len(str(today.month)) == 2:
	month = str(today.month)
else:
	month = "0" + str(today.month)
if len(str(today.day)) == 2:
	day = str(today.day)
else:
	day = "0" + str(today.day)

datesuffix = year + month + day 


###############

# inputs/parameters:

# which tracks to run - all or just mains? - pick one 	# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< PARAMETER - PICK ONE
##	tracks_needed = "AllTracks"  		# <<<<<<<<< USE THIS IF RUNNING ALL TRACKS
tracks_needed = "Mains_Sidings"  	# <<<<<<<<< USE THIS IF RUNNING ONLY MAIN & SIDING TRACKS	

	
######################
# GDBs:

# path to local copies of GISPR input data
localgdb = "C:/MWLlocal/local_copies_reference_data/local_copies.gdb"

# gdb for input speed restriction replica data
speedgdb = "C:/MWLlocal/local_copies_reference_data/SPEEDRESTRICTION_inputs.gdb"

# gdb location for input templates
projectinputgdb = "C:/MWLlocal/SpeedLookupTable_local/SpeedLookupTable_inputs.gdb"

# speed lookup table project gdb
projectgdb = "C:/MWLlocal/SpeedLookupTable_local/SpeedLookupTable_output_local.gdb"


######################
# input data:

# tracksegment input data (from GISPR)  # always same
tracksegment = 		localgdb + "/" + "ITGIS_TRACKSEGMENT_local"


# subdivision input tables (from GISPR) - used for getting max speed for each subdiv  # always same
itgis_subdivision = localgdb + "/" + "ITGIS_SUBDIVISION_local"
utcs_subdivision = 	localgdb + "/" + "UTCS_SUBDIVISION_local"


# input template for ptclimit active table to be created
# MUST ALREADY EXIST IN GDB SPECIFIED
template_a = projectinputgdb + "/" + "template_segmenttable"	# <<< used in part # 2

# input template for speedtable to be created
# MUST ALREADY EXIST IN GDB SPECIFIED
template_b = projectinputgdb + "/" + "template_speedtable"	# <<< used in part # 3

# input template for consolidated speedtable to be created
# MUST ALREADY EXIST IN GDB SPECIFIED
template_c = projectinputgdb + "/" + "template_consolidated_speedtable"	# <<< used in part # 7


###############
# output prep

# set output location (to be workspace)
gdb = projectgdb

# set workspace
a.env.workspace = gdb


# file path for final excel output
excelpath = "C:/MWLlocal/SpeedLookupTable_local/excel_outputs"


# suffix used for file naming
filename_suffix = tracks_needed


# waypoint
print(str(datetime.datetime.now())[0:19] +" "+ "initial prep done")
# run time: <1 min.

################################################################################
################################################################################


# tracksegment data prep

# Make local copy of ITGIS_TRACKSEGMENT 
#   *as just table* - create new table and then populate it using cursors
#   (this process is alternative to using TableToTable)

# create new empty table which will become segmenttable
outpath = gdb
outname = segmenttable = ("SEGMENTTABLE_" + datesuffix + "_" + tracks_needed ) # + "_" + timesuffix)  # output table name   
template = template_a
a.CreateTable_management(outpath,outname,template)  
# ^ template_t defined at beginning
# ^ output will be located in gdb specified at beginning

# create empty list for rows to be inserted in new table
insertlist = []

# search cursor to get each row from input table

cursordata = tracksegment
cursorfields = ["ASSET_PK","DIVCODE","MASTERLINENAME","SUBDIVISIONID",
				"BEGINMILEPOST","ENDMILEPOST","TRACKTYPE","LRS_ROUTEID",]
# filter out bad data / null values in key fields
where1 = "(NOT SUBDIVISIONID = -1) AND "
where2 = "((NOT BEGINMILEPOST IS NULL) AND (NOT ENDMILEPOST IS NULL)) AND "
where3 = "(NOT MASTERLINENAME IS NULL) AND "
where4 = "(NOT LRS_ROUTEID IS NULL) AND "
where5 = "(DIVCODE IN ('04','08','62','72','76','94')) AND "

if tracks_needed == "AllTracks":
	where6 = "(NOT TRACKTYPE IS NULL)"  	# <<< will be used if running ALL TRACKS  
elif tracks_needed == "Mains_Sidings":
	where6 = "((TRACKTYPE LIKE '%MAIN%') OR (TRACKTYPE = 'PASSING SIDING'))"  	# <<< will be used if running ONLY MAIN & SIDING TRACKS 

whereclause = where1 + where2 + where3 + where4 + where5 + where6
with a.da.SearchCursor(cursordata,cursorfields,whereclause) as cursor:
	for row in cursor:
		segid = 	row[0]
		div = 		row[1]
		mln = 		row[2]
		subid = 	row[3]
		lmp = 		row[4]
		hmp = 		row[5]
		# speed = doesn't exist in tracksegment
		tracktype = row[6]
		lrs = 		row[7]
		
		# create row to write to new table
		insertlist.append([segid,div,mln,subid,lmp,hmp,tracktype,lrs])
		
del cursor


# insert cursor to write rows to new table 
icursordata = segmenttable
icursorfields = ["SEGMENTID","DIVCODE","MASTERLINENAME","SUBDIVISIONID",
				"BEGINMILEPOST","ENDMILEPOST","TRACKTYPE","LRS_ROUTEID",]
icursor = a.da.InsertCursor(icursordata,icursorfields)

for irow in insertlist:
	segid = 	irow[0]
	div = 		irow[1]
	mln = 		irow[2]
	subid = 	irow[3]
	lmp = 		irow[4]
	hmp = 		irow[5]
	# speed = doesn't exist in tracksegment
	tracktype = irow[6]
	lrs = 		irow[7]	
	
	# write row to new table
	icursor.insertRow((segid,div,mln,subid,lmp,hmp,tracktype,lrs))
	
del icursor



print(str(datetime.datetime.now())[0:19] +" "+ "segmenttable prep done")

################################################################################


for tt in  [
	"FREIGHT",
	"INTERMODAL",
	"PASSENGER",
	]:
		
	traintype = tt

	# speed restriction data prep

	# speed restriction input data (from GISPR) - dependent on traintype 
	restrictiondata = 	speedgdb + "/" + "SPEEDRESTRICTION_" + traintype	
	
	# Make local copy of PTCGIS.SPEEDRESTRICTION_[TRAINTYPE]
	#   *as just table* - create new table and then populate it using cursors
	#   (this process is alternative to using TableToTable)
	#   (for given traintype)
	
	# create new empty table which will become speedtable
	outpath = gdb
	outname = speedtable = ("SPEEDTABLE_" + datesuffix + "_" + traintype + "_" + filename_suffix) # + "_" + timesuffix)  # output table name   
	template = template_b
	a.CreateTable_management(outpath,outname,template)  
	# ^ template_s defined at beginning
	# ^ output will be located in gdb specified at beginning
	
	# create empty list for rows to be inserted in new table
	insertlist = []
	
	# search cursor to get each row from input table
	
	cursordata = restrictiondata
	cursorfields = ["SEGMENTID","MASTERLINENAME","SUBDIVISIONID",
			"BEGINMILEPOST","ENDMILEPOST","SPEED","LRS_ROUTEID",]
	# filter out bad data / null values in certain fields
	where1 = "(NOT SUBDIVISIONID = -1) AND "
	where2 = "((NOT BEGINMILEPOST IS NULL) AND (NOT ENDMILEPOST IS NULL)) AND "
	where3 = "(NOT MASTERLINENAME IS NULL) AND "
	where4 = "(NOT LRS_ROUTEID IS NULL) AND "
	# filter out restrictions not needed
	where5 = "(RESTRICTIONTYPE = 'Generic') AND "	## <<<<<<<<<<<<<<<<<<<<<<<<< ASSUME ONLY Generic FOR NOW! 		MAY REVISE LATER...
	where6 = "(HEADENDFLAG <> 'Y') AND "			## <<<<<<<<<<<<<<<<<<<<<<<<< ASSUME no HEADENDFLAG FOR NOW! 	MAY REVISE LATER...
	where7 = "(DIRECTION = 'Bidirectional')"		## <<<<<<<<<<<<<<<<<<<<<<<<< ASSUME ONLY BIDIRECTIONAL FOR NOW!	MAY REVISE LATER...	
	
	whereclause = where1 + where2 + where3 + where4 + where5 + where6 + where7
	with a.da.SearchCursor(cursordata,cursorfields,whereclause) as cursor:
		for row in cursor:
			segid = 	row[0]
			# div = field doesn't exist in input data - populate it after table is created
			mln = 		row[1]
			subid = 	row[2]
			lmp = 		row[3]
			hmp = 		row[4]
			speed = 	row[5]
			# tracktype = doesn't exist in input data - will be joined from tracksegment
			lrs = 		row[6]
			
			# create row to write to new table
			insertlist.append([segid,mln,subid,lmp,hmp,speed,lrs])
			
	del cursor
	
	
	# insert cursor to write rows to new table 
	icursordata = speedtable
	icursorfields = ["SEGMENTID","MASTERLINENAME","SUBDIVISIONID",
			"BEGINMILEPOST","ENDMILEPOST","SPEED","LRS_ROUTEID",]
	icursor = a.da.InsertCursor(icursordata,icursorfields)
	
	for irow in insertlist:
		segid = 	irow[0]
		# div = field doesn't exist in input data - populate it after table is created
		mln = 		irow[1]
		subid = 	irow[2]
		lmp = 		irow[3]
		hmp = 		irow[4]
		speed = 	irow[5]
		# tracktype = doesn't exist in input data - will be joined from tracksegment
		lrs = 		irow[6]	
		
		# write row to new table
		icursor.insertRow((segid,mln,subid,lmp,hmp,speed,lrs))
		
	del icursor
	


	print(str(datetime.datetime.now())[0:19] +" "+ "speedtable creation done"+  " for " + traintype)



	# populate DIVCODE in speedtable from middle 2 characters of masterlinename
	cursordata = speedtable
	cursorfields = ["DIVCODE","MASTERLINENAME"]
	with a.da.UpdateCursor(cursordata,cursorfields) as cursor:
		for row in cursor:
			mln = row[1]
			row[0] = mln[2:4]
			cursor.updateRow(row) 
	del cursor	
	
	# delete records with bad divcode
	cursordata = speedtable
	cursorfields = ["DIVCODE"]
	whereclause = "NOT DIVCODE IN ('04','08','62','72','76','94')"
	with a.da.UpdateCursor(cursordata,cursorfields,whereclause) as cursor:
		for row in cursor:
			cursor.deleteRow()
	del cursor	
	
				
	# Join TRACKTYPE from TRACKSEGMENT to SPEEDRESTRICTION 
	#   with SEGMENTID as key (=ASSET_PK in TRACKSEGMENT)
	intable = speedtable  # local copy of SPEEDRESTRICTION table for given traintype
	inkeyfield = "SEGMENTID"
	jointable = segmenttable  # local copy of TRACKSEGMENT table
	joinkeyfield = "SEGMENTID"
	joinfields = ["TRACKTYPE"]
	a.JoinField_management(intable,inkeyfield,jointable,joinkeyfield,joinfields)
	
		
	# delete records with null TRACKTYPE from speedtable
	#   (if tracksegment was filtered to only mains, then no tracktype
	#   will be joined for other tracks, so other tracks will also be
	#   eliminated from speed restrictions in this step)
	cursordata = speedtable
	cursorfields = ["TRACKTYPE"]
	whereclause = "TRACKTYPE IS NULL"
	with a.da.UpdateCursor(cursordata,cursorfields,whereclause) as cursor:
		for row in cursor:
			cursor.deleteRow()
	del cursor	


	print(str(datetime.datetime.now())[0:19] +" "+ "speedtable prep done"+  " for " + traintype)
	
	############################################################################
	
	# combine tracksegment & speed restrictions, more data prep
	
	# Append TRACKSEGMENT to SPEEDRESTRICTION (tracksegment features will serve 
	#   as dummy speed lines to fill places where there are no speed restrictions)
	#   Pre/suf will go away, that?s ok	
	intable = segmenttable
	targettable = speedtable
	a.Append_management(intable,targettable,"NO_TEST")


	print(str(datetime.datetime.now())[0:19] +" "+ "append segmenttable to speedtable done"+  " for " + traintype)
	
	
	# Populate SPEED for appended records with subdiv max speed for mains 
	
	# create list of subdiv IDs (all subdivs in speedtable)
	subdivlist = []
	
	cursordata = speedtable
	cursorfields = ["SUBDIVISIONID"]
	with a.da.SearchCursor(cursordata,cursorfields) as cursor:
		for row in cursor:
			sub = row[0]
			if sub in subdivlist:
				pass
			else:
				subdivlist.append(sub)
	del cursor			
	

	# populate speeds for mains within each subdiv ID
	for sub in subdivlist:
		
		# define max speed for subdiv + train type, from ITGIS + UTCS subdivision tables
					
		# get ASSET_PK value from ITGIS_SUBDIVISION
		itsub_cursordata = itgis_subdivision  # input data
		itsub_cursorfields = ["ASSET_PK"]
		where_clause = "SUBDIVISIONID = " + str(sub)
		with a.da.SearchCursor(itsub_cursordata, itsub_cursorfields, where_clause) as itsub_cursor:
			for itsub_row in itsub_cursor:  # assumes only one row per subdiv id. this should be ok.
				itsub_asset_pk = itsub_row[0] 
		del itsub_cursor
		
		# get max speeds for each train type from UTCS_SUBDIVISION
		ucursordata = utcs_subdivision  # input data
		ucursorfields = ["MAX_SPEED_FREIGHT","MAX_SPEED_INTERMODEL","MAX_SPEED_PASSENGER"]
			# ^ spelling "INTERMODEL" is the actual field name spelling, so this is ok.
		where_clause = "ASSET_PK = " + str(itsub_asset_pk)
		with a.da.SearchCursor(ucursordata, ucursorfields, where_clause) as ucursor:
			for urow in ucursor:
				if traintype == "FREIGHT":
					maxspeed = urow[0]
				elif traintype == "INTERMODAL":
					maxspeed = urow[1]
				elif traintype == "PASSENGER":
					maxspeed = urow[2]	
		del ucursor
		
		
		# populate speed for all mains in subdiv that don't already have speed
		cursordata = speedtable											 
		cursorfields = ["SPEED","SUBDIVISIONID"]
		whereclause = "(SPEED IS NULL) AND (TRACKTYPE LIKE '%MAIN%') AND (SUBDIVISIONID = " + str(sub) + ")"  # main tracks for subdiv
		with a.da.UpdateCursor(cursordata,cursorfields,whereclause) as cursor:
			for row in cursor:
				row[0] = maxspeed
				cursor.updateRow(row) 
		del cursor	
	
	
	#	> Populate appended records speed 99 for other tracks
	cursordata = speedtable
	cursorfields = ["SPEED"]
	whereclause = "(SPEED IS NULL) AND (NOT TRACKTYPE LIKE '%MAIN%')"  # other tracks
	with a.da.UpdateCursor(cursordata,cursorfields,whereclause) as cursor:
		for row in cursor:
			row[0] = 99  # INTEGER
			cursor.updateRow(row) 
	del cursor	
	
	
	print(str(datetime.datetime.now())[0:19] +" "+ "speed populating done"+  " for " + traintype)
	
	
	################################################################################
	################################################################################
	
	## At this point, you have a bunch of speed ranges layered on top of each other. 
	## They need to be converted into consetutive ranges with only the lowest speed...
	
	
	# build list of SEGMENTID values
	segmentlist = []
	scursordata = speedtable
	scursorfields = ["SEGMENTID"]
	with a.da.SearchCursor(scursordata,scursorfields) as scursor:
		for srow in scursor:
			sid = srow[0]
			if sid in segmentlist:
				pass
			else:
				segmentlist.append(sid)
	del scursor
	
	
	# Iterate through SEGMENTIDs: for each, split/compress into ranges with lowest speed, 
	# eliminating overlapping ranges, similar to splitting single/double ranges
	
	# create empty list for rows to be inserted
	insertlist = []
	
	# first for each segmentid, split each range at every mp to produce "stacks" of ranges where only speed is different...
	for segmentid in segmentlist:
		
		# build list of each lmp and hmp for all ranges within segmentid
		cursordata = speedtable
		cursorfields = ["SPEED","BEGINMILEPOST","ENDMILEPOST",  #"SPEEDSOURCE",  # "DIRECTION",  # << fields can vary within segment id
			"SEGMENTID","DIVCODE","MASTERLINENAME","SUBDIVISIONID","TRACKTYPE","LRS_ROUTEID"]  # << fields constant within each segment id
		whereclause = "SEGMENTID = " + str(segmentid)
		with a.da.UpdateCursor(cursordata,cursorfields,whereclause) as cursor:
			
			mplist = []
			for mprow in cursor:
				
				lmp = mprow[1]
				hmp = mprow[2]
				
				if lmp in mplist:
			 		pass
				else:
			 		mplist.append(lmp)
			 		
				if hmp in mplist:
		 			pass
				else:
		 			mplist.append(hmp)
	 			
				del lmp
				del hmp
	 			
		del cursor
		
		
		# NEED TO SORT mplist FROM LOW TO HIGH
		mplist.sort()
		
		 			
		# how many items in mp list?
		if len(mplist) <= 2:  # no split needed
			pass	
	
		else:  # at least one split needed
			
			# split each range at each mp value
			cursordata = speedtable
			cursorfields = ["SPEED","BEGINMILEPOST","ENDMILEPOST",  #"SPEEDSOURCE",  # "DIRECTION",  # << fields can vary within segment id
				"SEGMENTID","DIVCODE","MASTERLINENAME","SUBDIVISIONID","TRACKTYPE","LRS_ROUTEID"]  # << fields constant within each segment id
			whereclause = "SEGMENTID = " + str(segmentid)
			with a.da.UpdateCursor(cursordata,cursorfields,whereclause) as cursor:
								
				for row in cursor:
			
					speed = 		row[0]
					lmp = 			row[1]
					hmp = 			row[2]
					segid = 		row[3]
					div = 			row[4]
					mln = 			row[5]
					subid = 		row[6]
					tracktype = 	row[7]
					lrs = 			row[8]				
					
					mp_split_list = []
					for x in mplist:
						if lmp < x < hmp:
							# add x to mp_split_list
							mp_split_list.append(x)
						else:
							pass
	
					
					if len(mp_split_list) == 0:  # no splits neded for this row
						pass
				
					else:  # do split(s)
					
						splits_needed = len(mp_split_list)
						
						splitcount = 0
						
						for mp_split in mp_split_list:
							
							if splitcount == 0:  # do first split
								# set mp_end to be mp_split, update row
								mp_end = mp_split
								row[2] = mp_end
								cursor.updateRow(row)
								
								splitcount += 1
							
							elif 0 < splitcount < splits_needed:
								# prep intermediate row to be added
								mp_begin = mp_end  # begin is end of previous range (previous split point)
								mp_end = mp_split  # end is current split point
								insertlist.append([speed,mp_begin,mp_end,segid,div,mln,subid,tracktype,lrs])
								
								splitcount += 1
								
							else:
								pass
								
						# prep last row to be added
						mp_begin = mp_end	# <<<<<<<<<<<<<<<<<<<<<< error: "name 'mp_end' is not defined"
						mp_end = hmp
						insertlist.append([speed,mp_begin,mp_end,segid,div,mln,subid,tracktype,lrs])
						
			del cursor
		
	
	
	# use insert cursor to write added rows (completing split(s))
	icursordata = speedtable
	icursorfields = ["SPEED","BEGINMILEPOST","ENDMILEPOST",  #"SPEEDSOURCE",  # "DIRECTION",  # << fields can vary within segment id
			"SEGMENTID","DIVCODE","MASTERLINENAME","SUBDIVISIONID","TRACKTYPE","LRS_ROUTEID"]  # << fields constant within each segment id
	icursor = a.da.InsertCursor(icursordata,icursorfields)
	for irow in insertlist:
		ispeed =		irow[0]
		ilmp =			irow[1]
		ihmp =			irow[2]
		isegid = 		irow[3]
		idiv = 			irow[4]
		imln = 			irow[5]
		isubid = 		irow[6]
		itracktype = 	irow[7]
		ilrs = 			irow[8]
		
		icursor.insertRow((ispeed,ilmp,ihmp,isegid,idiv,imln,isubid,itracktype,ilrs))
	
	del icursor
	
	
	print(str(datetime.datetime.now())[0:19] +" "+ "speedtable split into stacks done"+  " for " + traintype)
	
	
	############################################################################
	
	
	# 6						
	# then for each segmentid + lmp + hmp combo, compare speeds within the "stack" and delete all but lowest speed.
	cursordata = speedtable  # input data
	cursorfields = ["SEGMENTID","BEGINMILEPOST","ENDMILEPOST"]  # don't need SPEED field here
	keep_list = []
	with a.da.UpdateCursor(cursordata, cursorfields, "", "", "",
							sql_clause=(None, "ORDER BY SPEED ASC")) as cursor:
							# ^ THIS IS CRUCIAL FOR KEEPING ONLY LOWEST SPEED! 
		for row in cursor:
			segidvalue = row[0]
			lmpvalue = row[1]
			hmpvalue = row[2]
			combo = str(segidvalue) + "_" + str(lmpvalue).replace(".","_") + "_" + str(hmpvalue).replace(".","_")
			if combo not in keep_list:
				keep_list.append(combo)
			elif combo in keep_list:
				cursor.deleteRow()
	del cursor
	
	
	print(str(datetime.datetime.now())[0:19] +" "+ "speedtable only lowest speed kept done"+  " for " + traintype)
	
	
	############################################################################
	
	
	# 7
	# You will have some adjacent ranges w/ different SEGMENTID but same speed 
	# > consolidate these within each LRS_ROUTEID & TRACKTYPE, 
	#   similar to consolidate ranges portion of single/double script. 
	# > This will create new table which will be final output.
	
	# CONSOLIDATE CONSECUTIVE RANGES (w/ identical LRS_ROUTEID, SPEED, TRACKTYPE)
	
	
	# add field SUBSET_TEMP
	intable = speedtable
	addfield = "SUBSET_TEMP"
	addtype = "TEXT"
	addlength = 40
	addalias = addfield
	a.AddField_management(intable,addfield,addtype,"","",addlength,addalias)
	
	# populate SUBSET_TEMP (combo of LRS_ROUTEID, SPEED, TRACKTYPE)
	cursordata = speedtable
	cursorfields = ["LRS_ROUTEID","SPEED","TRACKTYPE","SUBSET_TEMP"]
	with a.da.UpdateCursor(cursordata,cursorfields) as cursor:
		for row in cursor:
			lrs =		row[0]
			speed = 	row[1]
			track = 	row[2]
			subset_combo = str(lrs) + "_" + str(speed) + "_" + track
			row[3] = subset_combo
			cursor.updateRow(row)
		
	
	# define list of subsets to iterate through
	subsetlist = []
	cursordata = speedtable
	cursorfields = ["SUBSET_TEMP"]
	with a.da.SearchCursor(cursordata,cursorfields) as cursor:
		for row in cursor:
			subset = row[0]
			if subset in subsetlist:
				pass
			else:
				subsetlist.append(subset)
	del cursor
	
	
	# create new table to store consolidated ranges
	outpath = gdb
	outname = consolidated_speedtable = "CONSOLIDATED_SPEEDTABLE_" + datesuffix + "_" + traintype + "_" + filename_suffix  
	template = template_c
	a.CreateTable_management(outpath,outname,template)  
	# ^ template_c defined at beginning
	# ^ output will be located in gdb specified at beginning
	

	print(str(datetime.datetime.now())[0:19] +" "+ "consolidation prep done"+  " for " + traintype)
	
	
	# establish empty list for rows to be inserted into consolidated table
	insertlist = []
	
	
	# for each subset at a time, consolidate consecutive ranges
	for subset in subsetlist:
	
		cursordata = speedtable
		cursorfields = ["DIVCODE","MASTERLINENAME","LRS_ROUTEID","SUBDIVISIONID",
				"TRACKTYPE","BEGINMILEPOST","ENDMILEPOST","SPEED","SUBSET_TEMP"]
		whereclause = "SUBSET_TEMP = '" + subset + "'"  # limit to one subset at a time
		
		# how many rows in cursor?  ## (this part must be here, not under "with a.da.SearchCursor(...) as cursor:")
		cursorcount = len(list(i for i in a.da.SearchCursor(cursordata,cursorfields,whereclause))) 
		
		with a.da.SearchCursor(cursordata,cursorfields,whereclause,"",
								sql_clause=(None, "ORDER BY BEGINMILEPOST ASC")) as cursor:
								# ^ THIS IS CRUCIAL
								
			hmp_end = 0  # dummy variable to start with
			rowcount = 1
			
			for row in cursor:
				div = 		row[0]
				mln = 		row[1]
				lrs = 		row[2]
				subid = 	row[3]
				track = 	row[4]
				lmp = 		row[5]
				hmp = 		row[6]
				speed = 	row[7]
				subset = 	row[8]
				
	
				if rowcount < cursorcount:
	
					if hmp_end > 0:  					# <<<<<<<<<<< TypeError: '>' not supported between instances of 'NoneType' and 'int'
					# hmp_end is defined, so not first row in first sequence	
						
						if lmp == hmp_end:  # is consecutive w/ prev. record
						
							# lmp_begin stays as previously defined
							
							# redefine hmp_end
							hmp_end = hmp  
							
						
						elif (lmp < hmp_end and hmp <= hmp_end):  # duplicate mileage, ignore
						
							pass
							
							
						elif (lmp < hmp_end and hmp > hmp_end):  # overlapping mileage with higher hmp
						
							# lmp_begin stays as previously defined
						
							# redefine higher hmp as hmp_end
							hmp_end = hmp
						
						
						else:  # is not consecutive, and not overlapping w/ prev. record 
								# >> end prev. sequence and start new sequence
							
							# write range to consolidated table
							insertlist.append([div,mln,lrs,subid,track,lmp_begin,hmp_end,speed]) 
	
							# then redefine lmp_begin & hmp_end, starting new sequence
							lmp_begin = lmp
							hmp_end = hmp
							
					else: # first in first sequence 
					
						# define lmp_begin & hmp_end for first sequence
						lmp_begin = lmp
						hmp_end = hmp
						
						
					rowcount += 1
				
				
				elif rowcount == cursorcount:	# last row in cursor.  # or, could be first and only row
				
					if hmp_end > 0:  # hmp_end is defined, so not first row in sequence
					
						# write final range (and previous range if this one is not consecutive)
						
						if lmp == hmp_end:  # is consecutive w/ previous record >> end sequence and write final range
							
							# lmp_begin stays as previously defined
							
							# redefine hmp_end
							hmp_end = hmp
						
							# write final range
							insertlist.append([div,mln,lrs,subid,track,lmp_begin,hmp_end,speed])
							
						elif (lmp < hmp_end and hmp <= hmp_end):  # duplicate mileage, ignore and write final range
						
							pass
							
							# write previous range as final range
							insertlist.append([div,mln,lrs,subid,track,lmp_begin,hmp_end,speed])
							
							
						elif (lmp < hmp_end and hmp > hmp_end):  # overlapping mileage with higher hmp
						
							# lmp_begin stays as previously defined
						
							# redefine higher hmp as hmp_end
							hmp_end = hmp
							
							# write final range
							insertlist.append([div,mln,lrs,subid,track,lmp_begin,hmp_end,speed])
							
						
						else:  # is not consecutive w/ prev. record >> end prev. sequence, write prev. range and write final range
		
							# write prev. range to consolidated table
							insertlist.append([div,mln,lrs,subid,track,lmp_begin,hmp_end,speed]) 
		
							# then redefine lmp_begin & hmp_end, starting new sequence
							lmp_begin = lmp
							hmp_end = hmp
							
							# write final range
							insertlist.append([div,mln,lrs,subid,track,lmp_begin,hmp_end,speed]) 
							
	
					else:  # this is the first AND ONLY range
					
						lmp_begin = lmp
						hmp_end = hmp
						
						# write range
						insertlist.append([div,mln,lrs,subid,track,lmp_begin,hmp_end,speed])
						
		del cursor
		
	
	
	# use insert cursor to write results to consolidated table
	icursordata = consolidated_speedtable
	icursorfields = ["DIVCODE","MASTERLINENAME","LRS_ROUTEID","SUBDIVISIONID",
					"TRACKTYPE","BEGIN_MP","END_MP","SPEED"]
	icursor = a.da.InsertCursor(icursordata,icursorfields)
	
	for irow in insertlist:
		idiv =			irow[0]
		imln =			irow[1]
		ilrs =			irow[2]
		isubid = 		irow[3]
		itracktype = 	irow[4]
		ilmp = 			irow[5]
		ihmp = 			irow[6]
		ispeed = 		irow[7]
		
		icursor.insertRow((idiv,imln,ilrs,isubid,itracktype,ilmp,ihmp,ispeed))
	
	del icursor


	print(str(datetime.datetime.now())[0:19] +" "+ "consolidation done"+  " for " + traintype)
	
	
	############################################################################	
	
	
	# 8
	# final prep
	
	
	# Change any speeds of 99 to 15 (base speed where no restriction applies on other tracks)
	cursordata = consolidated_speedtable  # input data
	cursorfields = ["SPEED"]
	where_clause = "SPEED = 99"  # everything populated as such
	with a.da.UpdateCursor(cursordata, cursorfields, where_clause) as cursor:
		for row in cursor:
			row[0] = 15
			cursor.updateRow(row)	
	del cursor
	
	
	# populate PREFIX, SUFFIX from MASTERLINENAME
	# ^ fields already exist b/c they're part of the consolidated template
	cursordata = consolidated_speedtable  # input data
	cursorfields = ["MASTERLINENAME","PREFIX","SUFFIX"]
	with a.da.UpdateCursor(cursordata,cursorfields,) as cursor:
		for row in cursor:
			mln = row[0]
			pre = mln[0:2].replace("_","")
			suf = mln[4:6].replace("_","")
			row[1] = pre
			row[2] = suf
			cursor.updateRow(row)	
	del cursor
	

	print(str(datetime.datetime.now())[0:19] +" "+ "final prep done"+  " for " + traintype)
	
	############################################################################
	
	
	# 9
	# Table to excel
	intable = consolidated_speedtable
	outpath = excelpath
	outfile = outpath + "/" + "Consolidated_SpeedTable_" + datesuffix + "_" + traintype + "_" + filename_suffix + ".xls"  # path + filename  
	a.TableToExcel_conversion(intable,outfile)
	

	print(str(datetime.datetime.now())[0:19] +" "+ "excel output done" +  " for " + traintype)
	
	
############################################################################
## THAT'S ALL ##############################################################
############################################################################

