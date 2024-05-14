#!/bin/bash
echo "$(date): Executing POST request." >> /var/www/b-root/aroot/batch.log
curl -X POST https://sd-a-root.info/batch >> /var/www/b-root/aroot/batch.log 2>&1
