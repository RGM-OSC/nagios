%define name nagios
%define version 3.5.1
%define release 8.rgm
%define nnmmsg logger -t %{name}/rpm

Summary: Host/service/network monitoring program
Name: %{name}
Version: %{version}
Release: %{release}
License: GPL
Group: Application/System
Source0: %{name}-%{version}.tar.gz
Source1: imagepak-base.tar.gz 
Source2: %{name}-rgm.tar.gz
Patch0: 0001-do-not-copy-brokermodules.dif
Patch1: 0003-remove-rrs-feed.dif
Patch2: 0004-remove-updateversioninfo.dif
Patch3: 0005-start-without-hosts-or-services.dif
Patch4: 0006-fix_f5_reload_bug.dif
Patch5: 0007-fix_downtime_struct.dif
Patch6: 0008-fix-encoding-after-2-reloads.dif
Patch7: 0009-Corrected-comparison-operator-in-service-freshness-c.dif
Patch8: 0010-Fixed-bug-445-Adding-triggered-downtime-for-child-ho.dif
BuildRoot: %{_tmppath}/%{name}-buildroot
Requires: gd > 1.8, zlib, libpng, libjpeg, bash, grep, mailx
BuildRequires: gcc, gd-devel > 1.8, zlib-devel, libpng-devel, libjpeg-devel
BuildRequires: systemd
BuildRequires: rpm-macros-rgm

Requires(pre,post): systemd

%define nsusr %{rgm_user_nagios}
%define nsgrp %{rgm_group}
%define wwwusr %{rgm_user_httpd}
%define wwwgrp %{rgm_user_httpd}

#todo: remove
%define rgm_nagios_path %{rgm_path}/%{name}-%{version}


%description
Nagios is a program that will monitor hosts and services on your
network. It has the ability to email or page you when a problem arises
and when a problem is resolved. Nagios is written in C and is
designed to run under Linux (and some other *NIX variants) as a
background process, intermittently running checks on various services
that you specify.

The actual service checks are performed by separate "plugin" programs
which return the status of the checks to Nagios. The plugins are
available at http://sourceforge.net/projects/nagiosplug

This package provide core programs for nagios. The web interface,
documentation, and development files are built as separate packages


%package www
Group: Application/System
Summary: Provides the HTML and CGI files for the Nagios web interface.
Requires: %{name} = %{version}
Requires: webserver


%description www
Nagios is a program that will monitor hosts and services on your
network. It has the ability to email or page you when a problem arises
and when a problem is resolved. Nagios is written in C and is
designed to run under Linux (and some other *NIX variants) as a
background process, intermittently running checks on various services
that you specify.

Several CGI programs are included with Nagios in order to allow you
to view the current service status, problem history, notification
history, and log file via the web. This package provides the HTML and
CGI files for the Nagios web interface. In addition, HTML
documentation is included in this package


%package devel
Group: Application/System
Summary: Provides include files that Nagios-related applications may compile against.
Requires: %{name} = %{version}

%description devel
Nagios is a program that will monitor hosts and services on your
network. It has the ability to email or page you when a problem arises
and when a problem is resolved. Nagios is written in C and is
designed to run under Linux (and some other *NIX variants) as a
background process, intermittently running checks on various services
that you specify.

This package provides include files that Nagios-related applications
may compile against.


%prep
%setup -q
%patch0 -p1
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p1
#%patch6 -p1
#%patch7 -p1
#%patch8 -p1
%setup -D -T -a 1
%setup -D -T -a 2

%pre
# Create `nagios' user on the system if necessary
if /usr/bin/id %{nsusr} > /dev/null 2>&1 ; then
	: # user already exists
else
	/usr/sbin/groupadd %{nsgrp} > /dev/null 2>&1
	/usr/sbin/useradd -d /home/%{name} -s /bin/bash -c "%{nsusr}" -g "%{nsgrp}" %{nsusr} || \
		%nnmmsg Unexpected error adding user "%{nsusr}". Aborting install process.
fi
 
%preun
%systemd_preun nagios.service

%postun
%systemd_postun_with_restart nagios.service 

# Delete nagios user and group
# (if grep doesn't find a match, then it is NIS or LDAP served and cannot be deleted)
if [ $1 = 0 ]; then
	/bin/grep '^%{nsusr}:' /etc/passwd > /dev/null 2>&1 && /usr/sbin/userdel %{nsusr} || %nnmmsg "User %{nsusr} could not be deleted."
	/bin/grep '^%{nsgrp}:' /etc/group > /dev/null 2>&1 && /usr/sbin/groupdel %{nsgrp} || %nnmmsg "Group %{nsgrp} could not be deleted."
fi

%post
%systemd_post nagios.service

# rgm nagios symlink
ln -nsf %{rgm_nagios_path} %{rgm_path}/%{name}
chown -h nagios:rgm %{rgm_path}/%{name}

%post www
# If apache is installed, and we can find the apache user, set a shell var
wwwusr=`awk '/^[ \t]*User[ \t]+[a-zA-Z0-9]+/ {print $2}' /etc/httpd/conf/*.conf`
if [ "z" == "z$wwwusr" ]; then # otherwise, use the default
	wwwusr=%{wwwusr}
fi
# if apache user is not in nsgrp, add it
if /usr/bin/id -Gn $wwwusr 2>/dev/null | /bin/grep -q %{nsgrp} > /dev/null 2>&1 ; then
	: # $wwwusr (default: apache) is already in rgm group
else
	# first find apache primary group
	pgrp=`/usr/bin/id -gn $wwwusr 2>/dev/null`
	# filter apache primary group from secondary groups
	sgrps=`/usr/bin/id -Gn $wwwusr 2>/dev/null | /bin/sed "s/^$pgrp //;s/ $pgrp //;s/^$pgrp$//;s/ /,/g;"`
	if [ "z" == "z$sgrps" ] ; then
		sgrps=%{nsgrp}
	else
		sgrps=$sgrps,%{nsgrp}
	fi
	# modify apache user, adding it to nsgrp
	/usr/sbin/usermod -G $sgrps $wwwusr >/dev/null 2>&1
	%nnmmsg "User $wwwusr added to group %{nsgrp} so sending commands to Nagios from the command CGI is possible."
fi


%build
cd ../%{name}-%{version}
export PATH=$PATH:/usr/sbin
CFLAGS="$RPM_OPT_FLAGS" CXXFLAGS="$RPM_OPT_FLAGS" \
./configure \
	--with-cgiurl=/nagios/cgi-bin \
	--with-htmurl=/nagios \
	--with-lockfile=/var/run/nagios/nagios.pid \
	--with-nagios-user=%{nsusr} \
	--with-nagios-group=%{nsgrp} \
	--prefix=%{rgm_nagios_path} \
	--exec-prefix=%{rgm_nagios_path}/bin \
	--bindir=%{rgm_nagios_path}/bin \
	--sbindir=%{rgm_nagios_path}/sbin \
	--libexecdir=%{rgm_nagios_path}/plugins \
	--datadir=%{rgm_nagios_path}/share \
	--sysconfdir=%{rgm_nagios_path}/etc \
	--localstatedir=%{rgm_nagios_path}/var/log \
	--with-file-perfdata \
	--with-gd-lib=/usr/lib \
	--with-gd-inc=/usr/include \
	--with-template-extinfo

make all

# make daemonchk.cgi and event handlers
cd contrib
make
cd eventhandlers
for f in `find . -type f` ; do
	F=`mktemp temp.XXXXXX`
	sed "s=/usr/local/nagios/var/rw/=%{rgm_nagios_path}/var/log/rw/=; \
		s=/usr/local/nagios/libexec/eventhandlers/=%{rgm_nagios_path}/plugins/eventhandlers=; \
		s=/usr/local/nagios/test/var=%{rgm_nagios_path}/var/log=" ${f} > ${F}
	mv ${F} ${f}
done
cd ../..


%install
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT
install -d -m 0775 ${RPM_BUILD_ROOT}%{rgm_nagios_path}/var/log/spool/checkresults
install -d -m 0775 ${RPM_BUILD_ROOT}%{rgm_nagios_path}/var/log/rw
install -d -m 0755 ${RPM_BUILD_ROOT}/usr/include/nagios/
install -d -m 0755 ${RPM_BUILD_ROOT}/etc/logrotate.d
install -d -m 0755 ${RPM_BUILD_ROOT}/etc/httpd/conf.d
install -d -m 0665 ${RPM_BUILD_ROOT}%{rgm_nagios_path}/etc
install -d -m 0755 ${RPM_BUILD_ROOT}/var/run/nagios
install -d -m 0755 ${RPM_BUILD_ROOT}%{_unitdir}
install -d -m 0755 ${RPM_BUILD_ROOT}/usr/lib/tmpfiles.d/
install -d -m 0755 ${RPM_BUILD_ROOT}/etc/sysconfig/

make DESTDIR=${RPM_BUILD_ROOT} INSTALL_OPTS="" COMMAND_OPTS="" install
make DESTDIR=${RPM_BUILD_ROOT} INSTALL_OPTS="" COMMAND_OPTS="" INIT_OPTS="" 

# install headers for development package
install -m 0644 include/*.h ${RPM_BUILD_ROOT}/usr/include/nagios/

# install CGIs
cd contrib
make INSTALL=install DESTDIR=${RPM_BUILD_ROOT} INSTALL_OPTS="" COMMAND_OPTS="" CGIDIR=%{rgm_nagios_path}/sbin install
cd ..

# install event handlers
cd contrib/eventhandlers
install -d -m 0755 ${RPM_BUILD_ROOT}%{rgm_nagios_path}/plugins/eventhandlers
for file in * ; do
    test -f $file && install -m 0755 $file ${RPM_BUILD_ROOT}%{rgm_nagios_path}/plugins/eventhandlers && rm -f $file
done
cd ../..

# logos
cd imagepak-base
install -d -m0755 ${RPM_BUILD_ROOT}%{rgm_nagios_path}/share/images/logos
install -m0755 * ${RPM_BUILD_ROOT}%{rgm_nagios_path}/share/images/logos
# rgm specifics
cd ../%{name}-rgm
#todo: degage
#install -d -m0755 ${RPM_BUILD_ROOT}%{rgm_conf_path}
#cp -afpvr ./* ${RPM_BUILD_ROOT}%{rgm_conf_path}
cp -aprf etc/* ${RPM_BUILD_ROOT}%{rgm_nagios_path}/etc/
install -d -m0755 ${RPM_BUILD_ROOT}%{rgm_nagios_path}/share/stylesheets
install -m0664 stylesheets/* ${RPM_BUILD_ROOT}%{rgm_nagios_path}/share/stylesheets
cp -aprf images/* ${RPM_BUILD_ROOT}%{rgm_nagios_path}/share/images/
#install -m0664 nagios.conf ${RPM_BUILD_ROOT}%{_sysconfdir}/httpd/conf.d/nagios.conf
install -m0644 %{name}.service ${RPM_BUILD_ROOT}%{_unitdir}/%{name}.service
install -m0644 %{name}.conf.tmpfiles ${RPM_BUILD_ROOT}/usr/lib/tmpfiles.d/%{name}.conf
install -m0644 %{name}.sysconfig ${RPM_BUILD_ROOT}/%{_sysconfdir}/sysconfig/%{name}
install -m0754 rgm-nagios-archives.cron ${RPM_BUILD_ROOT}/%{_sysconfdir}/cron.daily/rgm-nagios-archives


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(0664,%{nsusr},%{nsgrp},0775)
%dir %{rgm_nagios_path}/etc
%dir %{rgm_nagios_path}/etc/objects
%{rgm_nagios_path}/etc/*
%{rgm_nagios_path}/etc/objects/*
#%attr(0664,%{nsusr},%{nsgrp}) %{rgm_nagios_path}/etc/*
#%attr(0664,%{nsusr},%{nsgrp}) %{rgm_nagios_path}/etc/objects/*
#%attr(0775,%{nsusr},%{nsgrp}) %{rgm_nagios_path}/etc/objects
#%attr(0775,%{nsusr},%{nsgrp}) %{rgm_nagios_path}/etc
%defattr(0644,root,root)
%attr(0644,root,root) %{_unitdir}/%{name}.service
%attr(0644,root,root) %{_sysconfdir}/sysconfig/%{name}
%attr(0754,root,root) %{_sysconfdir}/cron.daily/rgm-nagios-archives
%{rgm_nagios_path}/share/images/logos/*
%{rgm_nagios_path}/share/stylesheets/*
#%config(noreplace) %{_sysconfdir}/httpd/conf.d/nagios.conf	
/usr/lib/tmpfiles.d/%{name}.conf
%defattr(755,%{nsusr},%{nsgrp})
%dir %{rgm_nagios_path}
%dir %{rgm_nagios_path}/bin
%dir /var/run/nagios
%attr(0755,%{nsusr},%{nsgrp}) %{rgm_nagios_path}/bin/*
%dir %{rgm_nagios_path}/sbin
%dir %{rgm_nagios_path}/share
%dir %{rgm_nagios_path}/share/images/logos
%dir %{rgm_nagios_path}/share/stylesheets
%dir %{rgm_nagios_path}/plugins
%dir %{rgm_nagios_path}/plugins/eventhandlers
%attr(755,%{nsusr},%{nsgrp}) %{rgm_nagios_path}/plugins/eventhandlers/*
%dir %{rgm_nagios_path}/var
%dir %{rgm_nagios_path}/var/log
%dir %{rgm_nagios_path}/var/log/archives
%defattr(2775,%{nsusr},%{nsgrp})
%dir %{rgm_nagios_path}/var/log/rw
%dir %{rgm_nagios_path}/var/log/spool
%dir %{rgm_nagios_path}/var/log/spool/checkresults
%doc Changelog INSTALLING LICENSE README UPGRADING


%files www
%attr(755,%{nsusr},%{nsgrp}) %{rgm_nagios_path}/sbin/*
%attr(755,%{nsusr},%{nsgrp}) %{rgm_nagios_path}/share/*
%defattr(-,root,root)


%files devel
%defattr(-,root,root)
%dir /usr/include
/usr/include/nagios


%changelog

* Mon Aug 2 2021 Eric Belhomme <ebelhomme@fr.scc.com> - 3.5.1-8.rgm
- add rgm-nagios-archives cron job

* Wed Mar 17 2021 Eric Belhomme <ebelhomme@fr.scc.com> - 3.5.1-7.rgm
- remove apache config
- Add aruba logo

* Mon Jun 15 2020 Vincent Fricou <vincent@fricouv.eu> - 3.5.1-6.rgm
- Add logo Extreme Network and Hirshmann

* Fri Jun 11 2020 Michael Aubertin <maubertin@fr.scc.com> - 3.5.1-5.rgm
- Add 4ANY logo

* Fri May 29 2020 Michael Aubertin <maubertin@fr.scc.com> - 3.5.1-4.rgm
- Add RGM logo

* Thu Mar 21 2019 Eric Belhomme <ebelhomme@fr.scc.com> - 3.5.1-3.rgm
- add rpm-macros-rgm as build dependency
- fixed RGM paths

* Tue Mar 05 2019 Michael Aubertin <maubertin@fr.scc.com> - 3.5.1-3.rgm
- Initial fork

* Thu Jan 19 2017 Jean-Philippe Levy <jeanphilippe.levy@gmail.com> - 3.5.1-2.eon
- packaged for EyesOfNetwork appliance 5.1

* Mon Jan 18 2016 Jean-Philippe Levy <jeanphilippe.levy@gmail.com> - 3.5.1-1.eon
- packaged for EyesOfNetwork appliance 5.0

* Thu Sep 05 2013 Jean-Philippe Levy <jeanphilippe.levy@gmail.com> - 3.5.1-0.eon
- upgrade to version 3.5.1

* Thu Aug 22 2013 Jean-Philippe Levy <jeanphilippe.levy@gmail.com> - 3.5.0-1.eon
- OMD patches added

* Thu Apr 25 2013 Jean-Philippe Levy <jeanphilippe.levy@gmail.com> - 3.5.0-0.eon
- packaged for EyesOfNetwork appliance 4.0

* Fri Jul 20 2012 Guillaume ONA <guillaume.ona@gmail.com> - 3.4.1-1.eon
- Disable epn and bug fixes

* Tue May 29 2012 Jean-Philippe Levy <jeanphilippe.levy@gmail.com> - 3.4.1-0.eon
- upgrade to version 3.4.1

* Wed Nov 09 2011 Jean-Philippe Levy <jeanphilippe.levy@gmail.com> - 3.3.1-0.eon
- upgrade to version 3.3.1

* Mon Oct 04 2010 Jean-Philippe Levy <jeanphilippe.levy@gmail.com> - 3.2.3-0.eon
- upgrade to version 3.2.3

* Sun Sep 05 2010 Jean-Philippe Levy <jeanphilippe.levy@gmail.com> - 3.2.2-0.eon
- upgrade to version 3.2.2

* Wed Jul 28 2010 Jean-Philippe Levy <jeanphilippe.levy@gmail.com> - 3.2.1-1.eon
- packaged for EyesOfNetwork appliance 2.2

* Thu Mar 11 2010 Jean-Philippe Levy <jeanphilippe.levy@gmail.com> - 3.2.1-0.eon
- upgrade to version 3.2.1

* Mon Aug 17 2009 Jean-Philippe Levy <jeanphilippe.levy@gmail.com> - 3.2.0-0.eon
- upgrade to version 3.2.0

* Fri Jul 24 2009 Jean-Philippe Levy <jeanphilippe.levy@gmail.com> - 3.1.2-0.eon
- upgrade to version 3.1.2 

* Thu May 14 2009 Jean-Philippe Levy <jeanphilippe.levy@gmail.com> - 3.1.0-0.eon
- packaged for EyesOfNetwork appliance 2.0

* Mon Apr 13 2009 Jean-Philippe Levy <jeanphilippe.levy@gmail.com> - 3.0.6-1.eon
- packaged for EyesOfNetwork appliance 2.0 
- stylesheets modifications

* Tue Dec 02 2008 Jean-Philippe Levy <jeanphilippe.levy@gmail.com> - 3.0.6-0.eon
- packaged for EyesOfNetwork appliance

* Tue Nov 18 2008 Jean-Philippe Levy <jeanphilippe.levy@gmail.com> - 3.0.5-0.eon
- packaged for EyesOfNetwork appliance

* Fri Oct 17 2008 Jean-Philippe Levy <jeanphilippe.levy@gmail.com> - 3.0.4-0.eon
- packaged for EyesOfNetwork appliance

* Wed Sep 03 2008 Jean-Philippe Levy <jeanphilippe.levy@gmail.com> - 3.0.3-0.eon
- packaged for EyesOfNetwork appliance
