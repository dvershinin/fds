%if 0%{?amzn} >= 2 || 0%{?suse_version} >= 1315
%global python3_pkgversion 3
%endif

%global author Danila Vershinin - info@getpagespeed.com

%if 0%{?rhel} && 0%{?rhel} < 8
%bcond_with python3
%else
%bcond_without python3
%endif

%if 0%{?fedora} >= 30 || 0%{?rhel} >= 8
%bcond_with python2
%else
%bcond_without python2
# there are no Python 3 FirewallD bindings for EL7
%bcond_with python3
%endif

Name:           fds
Version:        0
Release:        1%{?dist}
Summary:        The go-to FirewallD CLI companion app
License:        BSD
URL:            https://github.com/dvershinin/fds
Source0:        https://github.com/dvershinin/fds/archive/v%{version}.tar.gz
Source1:        fds.cron

BuildArch:      noarch

%if %{with python2}
BuildRequires:  python2-devel
BuildRequires:  python2-six
BuildRequires:  python-netaddr
BuildRequires:  python2-tqdm
BuildRequires:  python2-cloudflare >= 2.7.1
BuildRequires:  python2-psutil
# will bring in msgpack and lockfile dependencies:
Requires:       python2-CacheControl
Requires:       python2-psutil
# For tests
BuildRequires:  python2-pytest
# Version extraction
BuildRequires:  python2-setuptools_scm_git_archive
%endif


%if %{with python3}
BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-six
BuildRequires:  python%{python3_pkgversion}-netaddr
BuildRequires:  python%{python3_pkgversion}-tqdm
BuildRequires:  python%{python3_pkgversion}-cloudflare >= 2.7.1
BuildRequires:  python%{python3_pkgversion}-psutil
# will bring in msgpack and lockfile dependencies:
Requires:       python%{python3_pkgversion}-CacheControl
Requires:       python%{python3_pkgversion}-psutil
# For tests
BuildRequires:  python%{python3_pkgversion}-pytest
# Version extraction
BuildRequires:  python%{python3_pkgversion}-setuptools_scm_git_archive
%endif


# For generation of man page
BuildRequires:  pandoc

# CLI app is Python 2 version if Python 2 is available, oterhwise Python 3
%if %{with python2}
Requires:       python2-%{name} = %{version}-%{release}
%else
Requires:       python%{python3_pkgversion}-%{name} = %{version}-%{release}
%endif
Requires:       conntrack-tools

%description
fds is the CLI wrapper for FirewallD/Cloudflare, that you'll love
to use any day.

%if %{with python2}
%package -n     python2-%{name}
Summary:        Python 2 module for %{name}
BuildArch:      noarch
Requires:       python2-setuptools
Requires:       python2-firewall
Requires:       python2-six
Requires:       python-netaddr
Requires:       python-ipaddress
Requires:       python2-tqdm
Requires:       python2-cloudflare >= 2.7.1
# will bring in msgpack and lockfile dependencies:
Requires:       python2-CacheControl
%{?python_provide:%python_provide python2-%{name}}

%description -n python2-%{name}
Python module for %{name}
%endif


%if %{with python3}
%package -n     python%{python3_pkgversion}-%{name}
Summary:        Python 3 module for %{name}
BuildArch:      noarch
Requires:       python%{python3_pkgversion}-setuptools
Requires:       python%{python3_pkgversion}-firewall
Requires:       python%{python3_pkgversion}-six
Requires:       python%{python3_pkgversion}-netaddr
Requires:       python%{python3_pkgversion}-tqdm
Requires:       python%{python3_pkgversion}-cloudflare >= 2.7.1
# will bring in msgpack and lockfile dependencies:
Requires:       python%{python3_pkgversion}-CacheControl
%{?python_provide:%python_provide python%{python3_pkgversion}-%{name}}

%description -n python%{python3_pkgversion}-%{name}
Python %{python3_pkgversion} module for %{name}
%endif


%prep
%setup -qn %{name}-%{version}
# add info section to README.md so it can be nicely converted to man page
sed -i '1i| %{name}(1)\n| %{author}\n| July 2019\n\n' README.md
# we package CacheControl with the fix so we do not need newer requests library:
sed -i 's@requests>=2.6.1@requests@' setup.py
# we do not need ipaddress module on Python 3, it's built-in
sed -i '/ipaddress;/d' setup.py


%check
# mock does not have networking on by default.
# py.test -v


%build
%if %{with python2}
%py2_build
%endif
%if %{with python3}
%py3_build
%endif
# generates man page
pandoc -s -t man README.md -o %{name}.1


%install
%if %{with python2}
%py2_install
%endif
%if %{with python3}
%py3_install
%endif
# Remove tests from install (not good folder)
rm -rf %{buildroot}%{python3_sitelib}/tests
rm -rf %{buildroot}%{python2_sitelib}/tests

%{__install} -Dpm0644 %{name}.1 \
    $RPM_BUILD_ROOT%{_mandir}/man1/%{name}.1

%{__mkdir} -p $RPM_BUILD_ROOT%{_localstatedir}/cache/%{name}
%{__mkdir} -p $RPM_BUILD_ROOT/var/lib/%{name}

%{__install} -D -m755 %{SOURCE1} %{buildroot}%{_sysconfdir}/cron.daily/%{name}


%postun
if [ $1 -eq 0 ]; then
    %{__rm} -rf %{_localstatedir}/cache/%{name}
fi


%files
%license LICENSE
%doc README.md
%{_bindir}/%{name}
%{_mandir}/man1/*.1*
%{_sysconfdir}/cron.daily/%{name}
%attr(0750,root,root) %dir %{_localstatedir}/cache/%{name}
%attr(0755, root, root)   %dir /var/lib/%{name}
#%%attr(0644, root, root) %%verify(not md5 size mtime) %%ghost %%config(missingok,noreplace) /var/lib/%%{name}/*


%if %{with python2}
%files -n python2-%{name}
%license LICENSE
%doc README.md
%{python2_sitelib}/*
%endif


%if %{with python3}
%files -n python%{python3_pkgversion}-%{name}
%license LICENSE
%doc README.md
%{python3_sitelib}/*
%endif


%changelog
* Thu Aug 15 2019 Danila Vershinin <info@getpagespeed.com>
- changelogs are not maintained
