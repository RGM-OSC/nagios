#!/bin/sh

# appliance group and use
APPLIANCEGRP="rgm"

# nagios paths
rgmdir="/srv/rgm"
linkdir="${rgmdir}/nagios"

chown -R nagios:${APPLIANCEGRP} ${linkdir}*
chmod 775 ${linkdir}/etc
chmod 775 ${linkdir}/etc/objects
chmod 775 ${linkdir}/var/log/spool/checkresults/

systemctl enable nagios.service &>/dev/null
systemctl start nagios.service &>/dev/null
/usr/sbin/usermod -g ${APPLIANCEGRP} -G apache nagios &>/dev/null
