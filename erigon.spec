# Disable the debug package as we don't provide it:
%global debug_package %{nil}
# TODO: rig up debug package support with golang.

%global git_commit 12889fd007a290c628c9a66e990c316bc5839eb1

Name:           erigon
Version:        2.55.1
Release:        %autorelease
Summary:        A very efficient next-generation Ethereum execution client
License:        LGPLv3
URL:            https://github.com/ledgerwatch/erigon

# File sources:
Source0:        https://github.com/ledgerwatch/%{name}/archive/v%{version}/%{name}-%{version}.tar.gz
Source1:        https://github.com/fedora-ethereum/%{name}-rpms/archive/v%{version}/%{name}-rpms-%{version}.tar.gz
# FIXME remove in the next release / tag
Source2:	erigon.tmpfiles.conf
BuildRequires: gcc >= 10
BuildRequires: gcc-c++ >= 10
BuildRequires: git
BuildRequires: golang
BuildRequires: golang-github-cpuguy83-md2man
BuildRequires: sed
BuildRequires: systemd-rpm-macros
Requires: firewalld-filesystem

%description
An implementation of Ethereum (aka "Ethereum execution client"), on the
efficiency frontier, written in Go, compatible with the proof-of-stake merge.


%prep
# Build fails with GCC Go, so die unless we can set that alternative:
%autosetup -b 0 -p1
%setup -a 1 -T -D -n %{name}-%{version}
sed -i -e "/go mod vendor/d" Makefile

%build
export GOPATH="${PWD}/go"
export PATH="${GOPATH}/bin:${PATH}"
export GIT_COMMIT="%{git_commit}"
export GIT_BRANCH="%{name}-v%{version}"
export GIT_TAG="v%{version}"
# Begin building:
echo "------------ Building Erigon $GIT_TAG from branch $GIT_BRANCH (commit $GIT_COMMIT) ------------"
make %{name} downloader hack integration observer rpcdaemon rpctest sentry state txpool
echo '# "%{name}" 1 "%{summary}" %{vendor} "User Manuals"' > %{name}.1.md
cat %{name}.1.md README.md | go-md2man > %{name}.1
#%%{__gzip} %%{name}.1
%{__rm} %{name}.1.md
# Rename binaries with common names to [name]-[binary] scheme:
cd build/bin
for binary in *; do
    %{__strip} --strip-debug --strip-unneeded ${binary}
    if echo ${binary} | grep -qv '^%{name}'; then
        %{__mv} ${binary} %{name}-${binary}
    fi
done
# Trash the temporary Go build chain:
chmod -R ug+w ${GOPATH}
rm -rf ${GOPATH}

%install
%{__install} -m 0755 -D ./build/bin/* -t %{buildroot}%{_bindir}
%{__install} -m 0644 -D ./%{name}.1   -t %{buildroot}%{_mandir}/man1
%{__install} -m 0644 -D ./%{name}-rpms-%{version}/units/*.service    -t %{buildroot}%{_prefix}/lib/systemd/system
%{__install} -m 0644 -D ./%{name}-rpms-%{version}/firewallsvcs/*.xml -t %{buildroot}%{_prefix}/lib/firewalld/services
%{__install} -m 0644 -D ./%{name}-rpms-%{version}/sysconfig/%{name}  -T %{buildroot}%{_sysconfdir}/sysconfig/%{name}
#%%{__install} -m 0644 -D ./%{name}-rpms-%{version}/tmpfiles/%{name}.conf  -T %{buildroot}%{_tmpfilesdir}/%{name}.conf
%{__install} -m 0644 %{SOURCE2}  -T %{buildroot}%{_tmpfilesdir}/%{name}.conf
# And create /var/lib/erigon
%{__install} -d %{buildroot}%{_sharedstatedir}/%{name}


%pre
getent group %{name} > /dev/null || groupadd -r %{name}
getent passwd %{name} > /dev/null || useradd -r -g %{name} -d %{_sharedstatedir}/%{name} -s /sbin/nologin -c "erigon user" %{name}

%post
#%%systemd_post et.service
%firewalld_reload

%preun
#%%systemd_preun et.service

%postun
#%%systemd_postun_with_restart et.service
%firewalld_reload


%files
%license COPYING COPYING.LESSER
%doc AUTHORS README.md TESTING.md
%{_bindir}/*
%{_mandir}/man1/%{name}.1*
%{_prefix}/lib/firewalld/services/%{name}-*.xml
%{_prefix}/lib/firewalld/services/%{name}.xml
%{_tmpfilesdir}/%{name}.conf
%{_unitdir}/%{name}-*service
%{_unitdir}/%{name}.service
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%dir %attr(-,%{name},%{name}) %{_sharedstatedir}/%{name}


%changelog
%autochangelog
