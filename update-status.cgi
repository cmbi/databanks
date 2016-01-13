#!/usr/bin/perl

use warnings;
use strict;
use File::stat;
use POSIX qw(strftime);
use CGI;
use CGI::Carp qw(fatalsToBrowser);

use Data::Dumper;

my $q = new CGI;
my $status_dir = "/data/status/";

open(my $fh, "<$status_dir/failed_dbs.txt");
my %failed_dbs = map { chomp($_); $_ => 1 } <$fh>;
close $fh;

my $update_active = -f "$status_dir/UPDATE_LOCK";

my $sort_js=<<'EOF';

var myCookie;

function orderBy(by)
{
    var table = document.getElementById("tabel");
    var rows = table.rows;
    if (rows == null)
        return;

    var rowArray = [];
    for (var i = 1; i < rows.length - 1; ++i)
        rowArray[i - 1] = rows[i];
    var backupRow = rows[rows.length - 1];

    rowArray.sort(function (a, b) {
        var d = 0;

        var dbA = a.attributes.getNamedItem("m2:" + by);
        var dbB = b.attributes.getNamedItem("m2:" + by);

		if (dbA != null && dbB != null)
		{
			if (dbA.value > dbB.value)
				d = -1;
			else if (dbA.value < dbB.value)
				d = 1;
		}
		else if (dbA != null)
			d = -1;
		else
			d = 1;
		
		if (by == 'name')
			d = -d;

        return d;
    });

    for (var i = 0; i < rowArray.length; ++i)
        table.appendChild(rowArray[i]);
    table.appendChild(backupRow);
    
    myCookie.order = by;
    myCookie.store();
}

function loaded()
{
	myCookie = new Cookie(document, "status-cookie", 240);
	if (! myCookie.load())
		myCookie.order = 'name';
	else
		orderBy(myCookie.order);
}
EOF

my %html_options = (
	-title=>"databanks @ $ENV{SERVER_NAME}",
	-script=>[
		{'src'=>"http://mrs.cmbi.ru.nl/mrs-5/scripts/mrs.js"},
		{'code'=>$sort_js, 'type'=>'text/javascript' }
	],
	-onload=>'loaded()',
	-head=>$q->meta({-http_equiv => 'refresh', -content => 30}),
	-style=>{'src'=>"../red-barn.css"}
);

if ($q->param('reset'))
{
	my $db = $q->param('reset');

	delete $failed_dbs{$db};

	open($fh, ">$status_dir/failed_dbs.txt") or die "Could not write to failed_dbs.txt";
	print $fh join("\n", keys %failed_dbs), "\n";
	close($fh);

	foreach my $st (
						'fetch', 'data', 'crawl'
					)
	{
		open(my $h, ">$status_dir/$db.${st}_done");
		print $h "touch\n";
		close($h);
	}
	
	print $q->redirect('update-status.cgi');
	exit(0);
}

my $text;
if ($q->param('log')) {
	if ($q->param('log') eq 'backup') {
		$text = &backup_log($q->param('nr'));
	} else {
		$text = &log($q->param('log'), $q->param('type'), $q->param('nr'));
	}
}
else {
	$text = &list();
}

print
#	$q->header(-Refresh=>'60', -charset=>'utf-8'),
	$q->header(-charset=>'utf-8'),
	$q->start_html(%html_options),
	'<div id="main">',
		$q->h4(
			$update_active ? "Automatic update is currently running" : "No update running at this time"
		),
		$text,
	'</div>',
	$q->end_html;

sub backup_log
{
	my ($nr) = @_;
	my ($log_file, $title, $log);
	
	$log_file = "backup.mirror_log";
	$log_file = "$log_file.$nr" if ($nr);
	$title = "Backup log";
		
	open(my $h, "$status_dir/$log_file") or die "Could not open logfile";
	while (<$h>) {
		s/&/&amp;/;
		s/</&lt;/;
		s/>/&gt;/;
		$log .= $_;
	}
	close $h;

	my ($link_older, $link_newer);
	
	if (not defined $nr or $nr < 3) {
		$link_older = $q->a({-href=>sprintf("?log=backup&nr=%d", $nr + 1)}, "next");
	}

	if ($nr) {
		$link_newer = $q->a({-href=>sprintf("?log=backup&nr=%d", $nr - 1)}, "previous");
	}
	else {
		$link_newer = "previous";
	}
	
	return $q->span(
		$q->div({-class=>'nav'},
			$link_newer,
			$link_older ? $link_older : "next",
		),
		$q->h3($title),
		$q->pre(
			$log
		)
	);
	
	return $text;	
}

sub log
{
	my ($db, $type, $nr) = @_;
	my ($log_file, $title);
	
	if ($type eq "fetch") {
		$log_file = "$db.fetch_log";
		$title = "Fetch log for $db";
	}
	elsif ($type eq "data") {
		$log_file = "$db.data_log";
		$title = "Data log for $db";
	}
	elsif ($type eq "crawl") {
		$log_file = "$db.crawl_log";
		$title = "Crawl log for $db";
	}
	
	$log_file = "$log_file.$nr" if ($nr);
	
	my $log;
		
	open LOG, "$status_dir/$log_file" or die "Could not open logfile";
	while (<LOG>) {
		s/&/&amp;/;
		s/</&lt;/;
		s/>/&gt;/;
		$log .= $_;
	}
	close LOG;

	my ($link_older, $link_newer);
	
	if (not defined $nr or $nr < 3) {
		$link_older = $q->a({-href=>sprintf("?log=$db&type=$type&nr=%d", $nr + 1)}, "next");
	}

	if ($nr) {
		$link_newer = $q->a({-href=>sprintf("?log=$db&type=$type&nr=%d", $nr - 1)}, "previous");
	}
	else {
		$link_newer = "previous";
	}
	
	return $q->span(
		$q->div({-class=>'nav'},
			$link_newer,
			$link_older ? $link_older : "next",
		),
		$q->h3($title),
		$q->pre(
			$log
		)
	);
	
	return $text;	
}

sub logData
{
	my ($file, $action, $log_date, $done_date) = @_;
	
	return 
		$log_date != 0 ? 
		(
			$q->td({-class=>(($log_date > $done_date + 1) ? "active" : undef)},
				strftime("%d-%b-%Y, %H:%M:%S", localtime($log_date))),
			$q->td({-class=>(($log_date > $done_date + 1) ? "active" : undef)},
				$q->a({-href=>"?log=$file&type=$action"}, "log")
			)
		)
		:
		(
			$q->td(),
			$q->td()
		);
}

sub list
{
	my @rows;
	
	push @rows, $q->Tr(
			$q->th({-width=>'12%', -colspan=>2, onClick=>'orderBy("name");'}, "name"),
			$q->th({-width=>'22%', -colspan=>2, onClick=>'orderBy("fetch");'}, "last fetch"),
			$q->th({-width=>'22%', -colspan=>2, onClick=>'orderBy("data");'}, "last data"),
			$q->th({-width=>'22%', -colspan=>2, onClick=>'orderBy("crawl");'}, "last crawl"),
		);
	
	opendir(my $dh, $status_dir) or die "can't opendir $status_dir: $!";
	my @files = sort grep { s/\.fetch_log$// } readdir($dh);
	closedir $dh;
	
	my $class;

	foreach my $file (@files)
	{
		my ($fetch_log_date, $fetch_done_date, $data_log_date, $data_done_date, $crawl_log_date, $crawl_done_date);
		
		$class = '';

		$fetch_log_date		= 0;
		$fetch_done_date	= 0;
		$data_log_date		= 0;
		$data_done_date		= 0;
		$crawl_log_date		= 0;
		$crawl_done_date	= 0;
	
		eval
		{
			$fetch_log_date		= stat("$status_dir/$file.fetch_log")->mtime;
			$fetch_done_date	= stat("$status_dir/$file.fetch_done")->mtime;
			$data_log_date		= stat("$status_dir/$file.data_log")->mtime;
			$data_done_date		= stat("$status_dir/$file.data_done")->mtime;
			$crawl_log_date		= stat("$status_dir/$file.crawl_log")->mtime;
			$crawl_done_date	= stat("$status_dir/$file.crawl_done")->mtime;
		};
		
		if ($failed_dbs{$file}) {
			$class = "error";
		}
		elsif ($update_active and (
			$fetch_done_date + 1 < $fetch_log_date or
			$data_done_date + 1 < $data_log_date or
			$crawl_done_date + 1 < $crawl_log_date))
		{
			$class = "active";
		}
		
		push @rows, $q->Tr(
			{
				-class=>$class,
				-'m2:name'=>$file,
				-'m2:fetch'=>strftime("%F %H:%M:%S", localtime($fetch_log_date)),
				-'m2:data'=>strftime("%F %H:%M:%S", localtime($data_log_date)),
				-'m2:crawl'=>strftime("%F %H:%M:%S", localtime($crawl_log_date))
			},

			$q->td($file),
			$q->td(
				$failed_dbs{$file} ? $q->a({-href=>"?reset=$file"}, "reset") : "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
			),
			&logData($file, "fetch", $fetch_log_date, $fetch_done_date),
			&logData($file, "data", $data_log_date, $data_done_date),
			&logData($file, "crawl", $crawl_log_date, $crawl_done_date)
		);
	}

	# backup
	my ($backup_log_date, $backup_done_date);

	eval
	{
		$backup_log_date	= stat("$status_dir/backup.mirror_log")->mtime;
		$backup_done_date	= stat("$status_dir/backup.mirror_done")->mtime;
	};

	$class = '';
	if ($failed_dbs{'backup'}) {
		$class = "error";
	}
	elsif (#$update_active and
		   $backup_done_date + 1 < $backup_log_date)
	{
		$class = "active";
	}
	
	push @rows, $q->Tr(
			{ -class=>$class },

			$q->td({-colspan=>2}, "backup"),
			&logData("backup", "backup", $backup_log_date, $backup_done_date),
#			&logData($file, "data", $data_log_date, $data_done_date),
#			&logData($file, "mrs", $mrs_log_date, $mrs_done_date)
		);
	
	return
		$q->div({-class=>'list'},
				'<div xmlns:m2="http://mrs.cmbi.ru.nl/mrs-web/nl/my-ns">',
				$q->table({-cellspacing=>'0', -cellpadding=>'0', -class=>'status', -id=>'tabel'},
					$q->caption("Status for $ENV{'SERVER_NAME'} at ".strftime("%d-%b-%Y, %H:%M:%S", localtime)),
					@rows
				),
				'</div>'
			);
}
