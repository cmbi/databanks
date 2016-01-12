#!/bin/csh -f
# Written by Robbie P. Joosten
#
# Version 2.1 (2011-08-23)
# - Adapted script to work with WHAT_CHECK 8
# - Now writes WHY_NOT2 style comments.
#
setenv PDBID $1
set D2 = `echo $PDBID | cut -c 2-3`
set DATE    = `date +'%G%m%d'` 

#Set main variables
setenv BASE   /data
setenv WHYNOT /data/scratch/whynot2/comment/${DATE}WC.txt
setenv PDB    /data/pdb/flat   
setenv WCWORK /data/tmp/wctemp			      #WHAT_CHECK workdir
setenv OUTPUT $BASE/pdbreport		          #Directory with the final results
setenv WC     /data/whatcheck				  #whatcheck dir
#setenv PATH   /data/whatcheck/scatterdir:$PATH
#echo $PATH


echo
echo "Evaluating PDB-entry $PDBID"
echo

#Create directories
if (-d $WCWORK/$PDBID) then
  rm -rf $WCWORK/$PDBID    #Delete previous temporary directories
endif
mkdir -p $WCWORK/$PDBID


#Go to temporay running directory
cd $WCWORK/$PDBID

#Get the PDB file
cp $PDB/pdb$PDBID.ent .

#Do the actual validation
if (-e pdb$PDBID.ent) then
  $WC/DO_WHATCHECK.COM pdb$PDBID.ent y y y >& log.log
else
  exit(1)
endif
  
#Check for an output file
if (-e pdbout.txt) then
  #Do Nothing
else
  #Create Whynot entry and die
  echo "Validation failed."
  if (`grep -c 'No protein/DNA/RNA read from input file' log.log` != 0) then
    echo "COMMENT: Too few normal (amino or nucleic acid) residues found" >> $WHYNOT
  else if (`grep -c 'STRUCTURE FAR TOO BAD' log.log` != 0) then
    echo "COMMENT: Just too bad" >> $WHYNOT
  else if (`grep -c 'You overloaded the soup' log.log` != 0) then
    echo "COMMENT: Just too big" >> $WHYNOT  
  else
    echo "COMMENT: WHAT_CHECK: general error" >> $WHYNOT
  endif
  echo "PDBREPORT,$PDBID" >> $WHYNOT
  cd $BASE
  exit(1)
endif
#Create webpage
$WC/dbdata/pdbout2html

#Check index.html completeness
if (`grep -c "Final summary" pdbout.html` == 0) then
  echo "Validation failed."
  if (`grep -c 'No protein/DNA/RNA read from input file' log.log` != 0) then
    echo "COMMENT: Too few normal (amino or nucleic acid) residues found" >> $WHYNOT   
  else if (`grep -c 'STRUCTURE FAR TOO BAD' log.log` != 0) then
    echo "COMMENT: Just too bad" >> $WHYNOT
  else if (`grep -c 'You overloaded the soup' log.log` != 0) then
    echo "COMMENT: Just too big" >> $WHYNOT  
  else if (`grep -c 'Too many backbone atoms have zero occupancy' log.log` != 0) then
    echo "COMMENT: Too few normal (amino or nucleic acid) residues found" >> $WHYNOT     
  else
    echo "COMMENT: WHAT_CHECK: general error" >> $WHYNOT   
  endif
  echo "PDBREPORT,$PDBID" >> $WHYNOT   
  cd $BASE
  exit(1)
endif

#Create PDBREPORT entry
mkdir -p $OUTPUT/$D2/$PDBID
mv -f pdbout.html $OUTPUT/$D2/$PDBID/index.html
mv -f pdbout.txt $OUTPUT/$D2/$PDBID/
mv -f pdb${PDBID}_ION.OUT $OUTPUT/$D2/$PDBID/$PDBID.ion
bzip2 check.db
mv -f check.db.bz2 $OUTPUT/$D2/$PDBID/
mv *.gif $OUTPUT/$D2/$PDBID/

#If successful, remove tempdir
rm -rf $WCWORK/$PDBID

#Go to start directory
cd $BASE

