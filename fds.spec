%if 0%{?amzn} >= 2
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
Summary:        The go-to FirewallD CLI app
License:        BSD
URL:            https://github.com/dvershinin/fds
Source0:        https://github.com/dvershinin/fds/archive/v%{version}.tar.gz

BuildArch:      noarch

%if %{with python2}
BuildRequires:  python2-devel
BuildRequires:  python2-six
# For tests
BuildRequires:  python2-pytest
%endif

%if %{with python3}
BuildRequires:  python%{python3_pkgversion}-devel
# For tests
BuildRequires:  python%{python3_pkgversion}-pytest
BuildRequires:  python%{python3_pkgversion}-six
%endif

# For generation of man page
BuildRequires:  pandoc

# CLI app is Python 2 version if Python 2 is available, oterhwise Python 3
%if %{with python2}
Requires:       python2-%{name} = %{version}-%{release}
%else
Requires:       python%{python3_pkgversion}-%{name} = %{version}-%{release}
%endif

%description
fds is the CLI wrapper for FirewallD/Cloudflare, that you'll love
to use any day.

%if %{with python2}
%package -n     python2-%{name}
Summary:        Python 2 module for %{name}
BuildArch:      noarch
Requires:       python2-six
%{?python_provide:%python_provide python2-%{name}}
 
%description -n python2-%{name}
Python module for %{name}
%endif


%if %{with python3}
%package -n     python%{python3_pkgversion}-%{name}
Summary:        Python 3 module for %{name}
BuildArch:      noarch
Requires:       python%{python3_pkgversion}-six
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
 
 
%files
%license LICENSE
%doc README.md
%{_bindir}/%{name}
%{_mandir}/man1/*.1*


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
* Mon Sep 07 2020 Danila Vershinin <info@getpagespeed.com> 0-1
- release 0
