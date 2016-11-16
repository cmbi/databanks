#!/bin/sh

cd /srv/data/bin/
rm -f /srv/data/flags/*
/usr/local/bin/mrs-lock-and-run /srv/data/status/UPDATE_LOCK \
   ./update-databanks -rRk 2>&1 | mail -s chelonium-update cbaakman@cmbi.ru.nl
