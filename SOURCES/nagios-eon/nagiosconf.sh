#!/bin/sh

# appliance group and use
APPLIANCEGRP="eyesofnetwork"

# nagios paths
eondir="/srv/eyesofnetwork"
linkdir="${eondir}/nagios"

chown -R nagios:${APPLIANCEGRP} ${linkdir}*
chmod 775 ${linkdir}/etc
chmod 775 ${linkdir}/etc/objects
chmod 775 ${linkdir}/var/log/spool/checkresults/

systemctl enable nagios.service &>/dev/null
systemctl start nagios.service &>/dev/null
/usr/sbin/usermod -g ${APPLIANCEGRP} -G apache nagios &>/dev/null
