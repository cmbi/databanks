/*
	$Id: run_and_log.cpp,v 1.2 2002/10/25 10:26:46 dbman Exp $
	
	run and log is an app that executes a command and captures its
	output to a log file. Log files can be rotated. The exit code
	of the command is passed through to the calling app.
	
	This app is needed to better catch log output in makefiles
	that call other makefiles.

	Created by: Maarten Hekkelman, CMBI
	Date:		Friday October 25 2002
*/

/*-
 * Copyright (c) 2005-2009
 *      CMBI, Radboud University Nijmegen. All rights reserved.
 *
 * This code is derived from software contributed by Maarten L. Hekkelman
 * and Hekkelman Programmatuur b.v.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. All advertising materials mentioning features or use of this software
 *    must display the following acknowledgement:
 *        This product includes software developed by the Radboud University
 *        Nijmegen and its contributors.
 * 4. Neither the name of Radboud University nor the names of its
 *    contributors may be used to endorse or promote products derived
 *    from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE RADBOUD UNIVERSITY AND CONTRIBUTORS
 * ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
 * TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE UNIVERSITY OR CONTRIBUTORS
 * BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

#include <stdarg.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <errno.h>
#include <fstream>
#include <string>
#include <sys/stat.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>

using namespace std;

// prototypes

void usage();
void error(const char* msg, ...);
int open_log_file(string logfile, int rotate);

// implementation

void error(const char* msg, ...)
{
	va_list vl;
	
	va_start(vl, msg);
	vfprintf(stderr, msg, vl);
	va_end(vl);
	puts("");
	
	exit(1);
}

void usage()
{
	puts("");
	puts("run_and_log [-l logfile] [-r number] cmd ...");
	puts("    -l logfile    The logfile to write output to");
	puts("    -r number     Rotate logfiles and keep this many around");
	puts("");
	exit(1);
}

// open_log_file creates a new log file if needed and truncs it if otherwise
// If the rotate parameter is not equal to zero the older log files are
// renamed to mimic a rotate.

int open_log_file(string logfile, int rotate)
{
	if (rotate < 0 || rotate > 7)
		error("rotate number must be between 0 and 7");
	
	if (rotate)
	{
		string dest = logfile + '.' + char('0' + rotate);
		string source = dest;
		
		for (int i = rotate; i > 0; --i)
		{
			if (i > 1)
				--source[source.length() - 1];
			else
				source = logfile;

			struct stat st;
			
			if (stat(source.c_str(), &st) == 0 && rename(source.c_str(), dest.c_str()) == -1)
				error("could not rotate logfile %s: %s", source.c_str(), strerror(errno));
			
			dest = source;
		}
	}
	
	int logFD = open(logfile.c_str(), O_RDWR | O_CREAT | O_TRUNC, 0644);
	if (logFD < 0)
		error("Could not open logfile %s", optarg);

	return logFD;
}

int main (int argc, /*const */char* argv[])
{
	string logFile;
	int c, logFD = -1, rotate = 0;
	
// GNU zuigt!
#ifdef __GLIBC__
	const char kOptions[] = "+l:r:";
#else
	const char kOptions[] = "l:r:";
#endif

	while ((c = getopt(argc, argv, kOptions)) != -1)
	{
		switch (c)
		{
			case 'l':
				logFile = optarg;
				break;
			
			case 'r':
				rotate = atoi(optarg);
				break;
			
			case '?':
			case 'h':
			default:
				usage();
		}
	}

	// open a log file if needed, otherwise output will go to stdout/stderr

	if (logFile.length())
		logFD = open_log_file(logFile, rotate);
	
	pid_t pid = fork();

	if (pid < 0)
		error("Could not fork\n");
	
	if (pid == 0) // child process
	{
		if (logFD > -1)		// since we need a logfile, redirect stdout and stderr to our logfile
		{
			if (dup2(logFD, STDOUT_FILENO) < 0)
				error("Could not dup (%s)", strerror(errno));
			if (dup2(logFD, STDERR_FILENO) < 0)
				error("Could not dup (%s)", strerror(errno));
		}
		
		// now execute the command
		
		execvp(argv[optind], argv + optind);
		
		// should never get here:
		error("Could not launch %s\n", argv[optind]);
	}

	// if we reach this code we're the parent process

	int result = 0, status = 1;
	if (waitpid(pid, &result, 0) == -1)
		error("waitpid failed: %s", strerror(errno));
	
	if (WIFEXITED(result))
		status = WEXITSTATUS(result);
	
	printf("%s: %s\n", argv[optind], status ? "failed" : "success");
	return status;
}
