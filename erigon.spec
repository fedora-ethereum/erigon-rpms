# Disable the debug package as we don't provide it:
%global debug_package %{nil}
# TODO: rig up debug package support with golang.

# Supplementary files version:
%define spec_suppl_ver %{?suppl_ver}%{!?suppl_ver:0.2.0}

Name:           erigon
Vendor:         Ledgerwatch
Version:        2.42.0
Release:        %autorelease
Summary:        A very efficient next-generation Ethereum execution client
License:        LGPLv3
URL:            https://github.com/ledgerwatch/erigon

# File sources:
Source0:        https://github.com/%{vendor}/%{name}/archive/refs/tags/v%{version}.tar.gz
Source1:        https://github.com/kaiwetlesen/%{name}-release/archive/refs/tags/v%{spec_suppl_ver}.tar.gz

BuildRequires: binutils
BuildRequires: curl
BuildRequires: gcc >= 10
BuildRequires: gcc-c++ >= 10
BuildRequires: git
BuildRequires: golang
BuildRequires: golang-github-cpuguy83-md2man

%description
An implementation of Ethereum (aka "Ethereum execution client"), on the
efficiency frontier, written in Go, compatible with the proof-of-stake merge.


%prep
# Build fails with GCC Go, so die unless we can set that alternative:
%autosetup -b 1 -n %{name}-release-%{spec_suppl_ver}
%autosetup -b 0 -n %{name}-%{version}
# Apply git attributes to release code:
git clone --bare --depth 1 -b v%{version} https://github.com/%{vendor}/%{name}.git .git
git init
git checkout -f -b %{name}-v%{version} tags/v%{version}

%build
export GOPATH="${PWD}/go"
export PATH="${GOPATH}/bin:${PATH}"
echo "Where are we?"
pwd
echo %{_builddir}/%{name}-%{version}

cd %{_builddir}/%{name}-%{version}
export GIT_COMMIT="$(git rev-parse HEAD)"
export GIT_BRANCH="%{name}-v%{version}"
export GIT_TAG="v%{version}"
# Begin building:
echo "------------ Building Erigon $GIT_TAG from branch $GIT_BRANCH (commit $GIT_COMMIT) ------------"
make %{name} rpcdaemon sentry txpool downloader hack state integration observer rpctest
echo '# "%{name}" 1 "%{summary}" %{vendor} "User Manuals"' > %{name}.1.md
cat %{name}.1.md README.md | go-md2man > %{name}.1
%{__gzip} %{name}.1
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
cd -


%install
%define build_srcdir  %{_builddir}/%{name}-%{version}
%define suppl_srcdir   %{_builddir}/%{name}-release-%{spec_suppl_ver}
%{__install} -m 0755 -D -s   %{build_srcdir}/build/bin/*       -t %{buildroot}%{_bindir}
%{__install} -m 0644 -D      %{build_srcdir}/README.md         -t %{buildroot}%{_datadir}/doc/%{name}
%{__install} -m 0644 -D      %{build_srcdir}/TESTING.md        -t %{buildroot}%{_datadir}/doc/%{name}
%{__install} -m 0644 -D      %{build_srcdir}/COPYING*          -t %{buildroot}%{_datadir}/licenses/%{name}
%{__install} -m 0644 -D      %{build_srcdir}/AUTHORS           -t %{buildroot}%{_datadir}/licenses/%{name}
%{__install} -m 0644 -D      %{build_srcdir}/%{name}.1.gz      -t %{buildroot}%{_mandir}/man1
%{__install} -m 0644 -D      %{suppl_srcdir}/units/*.service    -t %{buildroot}%{_prefix}/lib/systemd/system
%{__install} -m 0644 -D      %{suppl_srcdir}/firewallsvcs/*.xml -t %{buildroot}%{_prefix}/lib/firewalld/services
%{__install} -m 0644 -D      %{suppl_srcdir}/sysconfig/%{name}  -T %{buildroot}%{_sysconfdir}/sysconfig/%{name}


%files
%license COPYING COPYING.LESSER AUTHORS
%doc README.md TESTING.md
%{_bindir}/*
%{_mandir}/man1/%{name}.1.gz
%{_prefix}/lib/systemd/system/*
%{_prefix}/lib/firewalld/services/*
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}


%pre
if ! getent group %{name} &> /dev/null; then
    groupadd -r %{name}
fi
if ! getent passwd %{name} &> /dev/null; then
    useradd -r -g %{name} -m -d %{_sharedstatedir}/%{name} -k /dev/null %{name}
fi


%changelog
%autochangelog
