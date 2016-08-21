#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pprint import pprint
import os, os.path
import urllib.request
import re
import shutil

TEMPDIR = os.path.join(os.getcwd(),"TEMP")
OUTDIR = os.path.join(os.getcwd(),"retro_saved")
os.makedirs(TEMPDIR,exist_ok=True)
os.makedirs(OUTDIR,exist_ok=True)

def write(s):
    sys.stdout.write(s)
    sys.stdout.flush()

def findPackagesForFile(fileName):
    """
    fileName = name of file, can contain regex (i.e.: /libc.so.6)
    """
    write("Finding related packages ... ")
    out = subprocess.check_output(["apt-file","search","-x",fileName])
    out = out.decode('ascii')

    packages = set()

    for line in out.split("\n"):
        if len(line.split(": ")) != 2:
            continue
        packages.add(line.split(": ")[0])

    write("[ Done ]\n")
    return packages
    

def findVersionsForPackage(package,arch=None):
    """
    i.e.: package = libc6
    arch = i386, amd64, etc
    """
    write("Finding versions for package {0} arch {1} ... ".format(package,arch))

    #rmadison -u ubuntu -a arch -r libc6-x32
    search = ["rmadison","-u","ubuntu"]
    
    if arch is not None:
        search += ["-a",arch]

    search += [package]
    
    out = subprocess.check_output(search).decode('ascii')

    versions = []

    for line in out.split("\n"):
        splitted = line.split("|")
        if len(splitted) == 1:
            continue

        versions.append({
            "package": package,
            "version": splitted[1].strip(),
            "osRelease": splitted[2].strip(),
            "osReleaseBase": splitted[2].strip() if "-" not in splitted[2] else splitted[2].split("-")[0].strip(),
            "archs": [splitted[3].strip()] if "," not in splitted[3] else [x.strip() for x in splitted[3].split(",")]
        })


    write("[ Done ]\n")

    return versions
    
def downloadAndSaveVersion(versions):
    
    for version in versions:

        if OS == "ubuntu":
            for arch in version['archs']:
                write("Downloading version {0} for Ubuntu {1} ... ".format(version['version'],version['osReleaseBase']))
                url = "https://launchpad.net/ubuntu/{0}/{1}/{2}/{3}".format(version["osReleaseBase"],arch,version['package'],version['version'])

                # Grab content for launch pad page
                f = urllib.request.urlopen(url)
                content = f.read().decode('ascii')
                f.close()
    
                # Scrape out the download link
                url = re.search("\"(https?://.*{0}.*?.deb)\"".format(version['package']),content)
                if url == None:
                    write("[ Fail -- No Download Link Found ]\n")
                    continue
            
                url = url.group(1)
            
                #outPath = os.path.join(OUTDIR,OS,version['osReleaseBase'],arch,version['version'])
                #outPathFile = os.path.join(outPath,os.path.basename(fName))
                #os.makedirs(outPath,exist_ok=True)
                outPath = OUTDIR
                outPathFile = os.path.join(OUTDIR,"{0}_{1}_{2}_{3}_{4}".format(OS,version['osReleaseBase'],arch,version['version'],os.path.basename(fName)))
                os.makedirs(outPath,exist_ok=True)
                

                # Download the file
                tmp_deb = os.path.join(TEMPDIR,"pkg.deb")
                urllib.request.urlretrieve(url, tmp_deb)
                write("[ Done ]\n")
                write("Extracting and saving ... ")
            
                # Just calling dpkg for now
                subprocess.check_output(["dpkg","-x",tmp_deb,TEMPDIR])

                # Copy out the matching file
                subprocess.check_output("find " + TEMPDIR + " | grep " + fName + " | xargs -I '{}' cp {} " + outPathFile,shell=True)

                write("[ Done ]\n")

                # Delete the info in the TEMP dir
                shutil.rmtree(TEMPDIR)
                os.makedirs(TEMPDIR)
                

        else:
            print("OS of {0} isn't supported yet.".format(os))


parser = argparse.ArgumentParser(description='Grab old versions of a file. (Ubuntu only for now)')

parser.add_argument('fileName', type=str, nargs=1,
                   help='Name of the file to grab old versions of.')
parser.add_argument('arch', type=str, nargs=1,
                   help='Architecture such as amd64, arm64, armhf, i386, powerpc, ppc64el, s390x')

OS = "ubuntu"

args = parser.parse_args()
fName = args.fileName[0]
fArch = args.arch[0]

# Find what package it's in
packages = findPackagesForFile(fName)

# Find the versions we know about
versions = []
for package in packages:
    versions.append(findVersionsForPackage(package,fArch))

downloadAndSaveVersion(versions[0])

