#!/usr/bin/python
import glob
import os
import sys
import getopt
import xml.etree.ElementTree as ET
import shutil
import argparse
import sqlite3

testList = []
testNames = []
#orgList = []
sourceDir = ""
destDir = ""
orgName = ""
fullDestDir = ""

#collect options and validate they are correct

parser = argparse.ArgumentParser()

parser.add_argument("-s", help="This is the source directory to search for tests in")
parser.add_argument("-d", help="Directory to copy tests to")
parser.add_argument("-n", help="Name of org, used to create subdir")
parser.add_argument("-c", help="Clean up dirs")
parser.add_argument("-x", help="makexml", action="store_true")
parser.add_argument("-db", help ="Add settings to db", action="store_true")
parser.add_argument("-l", help="List orgs", action="store_true")

#Create the needed directory
def makeDir(destDir):
	try:
		os.makedirs(destDir + orgName + "/classes")
	except OSError:
		if not os.path.isdir(destDir):
			raise
	return(destDir)

#Create a subfolder for the name of the org
def getFullDestDir(destDir):
	fullDestDir = destDir + orgName + "/classes"
	return fullDestDir

#Search for testMethod string in classes
def searchTest(testList):
	os.chdir(sourceDir)
	for files in glob.glob("*.*"):
		f=open(files, 'r')
		s=f.read()
		if 'testMethod' in s:
			testList.append(f.name)
			testList.append(f.name + "-meta.xml")
			testNames.append(f.name)

#Copy Tests to needed dir
def copyTest(testList):
	for x in testList:
        	shutil.copy2(sourceDir + x, getFullDestDir(destDir))

def checkOrgExists(orgName):
        conn = sqlite3.connect('orgs.db')
        c = conn.cursor()
        #find the org details
        c.execute("Select orgName, sourceDir, destDir FROM main where orgName = ?", (orgName,))
        existingOrg = c.fetchall()
	# If org exists then return a map of its values
	if existingOrg != []:
		for row in existingOrg:
			orgName, sourceDir, destDir = row
		return {'orgName':orgName, 'sourceDir':sourceDir, 'destDir': destDir } 
	# If it doesnt exist tell the user and exit
	else:
		print orgName + " doesnt exist"
		sys.exit(2)

def clean(orgName):
	# Call checkOrgExists and add needed values to variables
	orgDict = checkOrgExists(orgName)
	cleanOrg = orgDict['orgName']
	destDir = orgDict['destDir']
	# If dictionary comes back not blank execute a delete
	if orgDict != []:
	        conn = sqlite3.connect('orgs.db')
	        c = conn.cursor()
                c.execute("DELETE FROM main where orgName = ?", (cleanOrg,))
                conn.commit()
                conn.close()
                shutil.rmtree(destDir + cleanOrg)
		print cleanOrg + " deleted"
	else:
		print cleanOrg + "does not exist"	


def buildXML(testList):
	print 'bla'

def db(orgName, sourceDir, destDir):
	#Create insert string
	orgList = (orgName, sourceDir, destDir)
	#connect to DB
	conn = sqlite3.connect('orgs.db')
	c = conn.cursor()
	#create table if not exists and find org
	c.execute('''CREATE TABLE if not exists main(orgName, sourceDir, destDir)''')
	c.execute("SELECT orgName FROM main WHERE orgName =?", (orgName,))
	existingOrg = c.fetchall()
	#if org exists dont create, if not, create
	if existingOrg == []:
		c.execute("INSERT INTO main VALUES (?,?,?)", orgList)
		print "Org %s added" % orgName
	else:
		print "Org %s already exists" % orgName

	conn.commit()
	conn.close()

def listOrgs():
	conn = sqlite3.connect('orgs.db')
	c = conn.cursor()
	c.execute("SELECT * FROM main")
	listOrgs = c.fetchall()
	for line in listOrgs:
		print line 

#select correct path
if __name__ == '__main__':
	args = parser.parse_args()
	sourceDir = args.s
	destDir = args.d
	orgName = args.n
	cleanOrg = args.c	
#select correct path
	if args.s and args.n and args.d and args.db:
		db(orgName, sourceDir, destDir)
		makeDir(destDir)
		searchTest(testList)
		copyTest(testList)
	elif args.c:
		clean(cleanOrg)
	elif args.s and args.n and args.d and not args.db:
                makeDir(destDir)
                searchTest(testList)
                copyTest(testList)
	elif args.l:
		listOrgs()
	elif args.n:
		org = checkOrgExists(orgName)
		destDir = org['destDir']
		sourceDir = org['sourceDir']	
               	print org
		makeDir(destDir)
                searchTest(testList)
                copyTest(testList)
		#you need to find the org and then execute everything
	elif args.x:
		buildXML(testList)








