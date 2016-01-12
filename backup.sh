#!/bin/sh

cd /data/bin/
/usr/local/bin/mrs-lock-and-run /data/status/UPDATE_LOCK \
   ./update-databanks -rRk backup clean 2>&1 | mail -s cmbi4-backup cbaakman@cmbi.ru.nl
