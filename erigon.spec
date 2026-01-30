%global git_commit 9a898cf76896d02edb6fd42de0d4b4b4f78ce9d3

Name:           erigon
Version:        3.3.7
Release:        1%{?dist}
Summary:        A very efficient next-generation Ethereum execution client
License:        LGPL-3.0-only
URL:            https://github.com/ledgerwatch/erigon
VCS:            git:%{url}.git
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz
Source1:        https://github.com/fedora-ethereum/%{name}-rpms/archive/v%{version}/%{name}-rpms-%{version}.tar.gz
Source2:        erigon.sysusers
Patch:          erigon-0001-db-state-add-optional-throttle-to-MergeLoop-to-reduc.patch
Patch:          erigon-0002-db-downloader-make-torrent-generation-reproducible.patch
BuildRequires: firewalld-filesystem
BuildRequires: gcc >= 10
BuildRequires: gcc-c++ >= 10
BuildRequires: git
# Build fails with GCC Go, so die unless we can set that alternative:
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
%autosetup -b 0 -p1 -n %{name}-%{version}
%setup -a 1 -T -D -n %{name}-%{version}

%build
export GOPATH="${PWD}/go"
export PATH="${GOPATH}/bin:${PATH}"
export GIT_COMMIT="%{git_commit}"
export GIT_BRANCH="%{name}-v%{version}"
export GIT_TAG="v%{version}"

# Begin building:
echo "------------ Building Erigon $GIT_TAG from branch $GIT_BRANCH (commit $GIT_COMMIT) ------------"
make BUILD_TAGS=nosqlite,noboltdb,nosilkworm %{name} downloader hack integration rpcdaemon rpctest sentry state txpool
echo '# "%{name}" 1 "%{summary}" %{vendor} "User Manuals"' > %{name}.1.md
cat %{name}.1.md README.md | go-md2man > %{name}.1
%{__rm} %{name}.1.md
# Rename binaries with common names to [name]-[binary] scheme:
cd build/bin
for binary in *; do
    if echo ${binary} | grep -qv '^%{name}'; then
        %{__mv} ${binary} %{name}-${binary}
    fi
done
# Trash the temporary Go build chain:
chmod -R ug+w ${GOPATH}
rm -rf ${GOPATH}

%install
install -m 0755 -D ./build/bin/* -t %{buildroot}%{_bindir}
install -m 0644 -D ./%{name}.1   -t %{buildroot}%{_mandir}/man1
install -m 0644 -D ./%{name}-rpms-%{version}/units/*.service    -t %{buildroot}%{_prefix}/lib/systemd/system
install -m 0644 -D ./%{name}-rpms-%{version}/firewallsvcs/*.xml -t %{buildroot}%{_prefix}/lib/firewalld/services
install -m 0644 -D ./%{name}-rpms-%{version}/sysconfig/%{name}  -T %{buildroot}%{_sysconfdir}/sysconfig/%{name}
install -m 0644 -p -D ./%{name}-rpms-%{version}/tmpfiles/%{name}.conf  -T %{buildroot}%{_tmpfilesdir}/%{name}.conf
install -m 0644 -p -D %{SOURCE2} %{buildroot}%{_sysusersdir}/%{name}.conf

# And create /var/lib/erigon
install -d %{buildroot}%{_sharedstatedir}/%{name}

%pre
%sysusers_create_compat %{SOURCE2}

%post
%firewalld_reload

%preun

%postun
%firewalld_reload

%files
%license COPYING
%doc AUTHORS README.md
%{_bindir}/*
%{_mandir}/man1/%{name}.1*
%{_prefix}/lib/firewalld/services/%{name}-*.xml
%{_prefix}/lib/firewalld/services/%{name}.xml
%{_tmpfilesdir}/%{name}.conf
%{_sysusersdir}/%{name}.conf
%{_unitdir}/%{name}-*service
%{_unitdir}/%{name}.service
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%dir %attr(-,%{name},%{name}) %{_sharedstatedir}/%{name}

%changelog
%autochangelog
