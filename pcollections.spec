Name:		pcollections
Version:	5.0.0
Release:	1
Summary:	Persistent Java collections
Group:		Development/Java
License:	MIT
URL:		https://github.com/hrldcpr/pcollections
# Tag v%{version}. The Gradle wrapper jar is not in this archive.
Source0:	https://github.com/hrldcpr/pcollections/archive/refs/tags/v%{version}.tar.gz#/pcollections-%{version}.tar.gz
# Error Prone 2.50.0 requires this coordinate exactly.
Source1:	https://github.com/hrldcpr/pcollections/archive/refs/tags/v4.0.1.tar.gz#/pcollections-4.0.1.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem

%description
PCollections %{version} is a library of persistent and immutable
collection classes. 5.0.0 keeps the 4.0.2 TreePMap serialization fix
and makes OrderedPMap.containsKey and OrderedPSet.contains use the id
map. The 4.0.1 jar stays installed because error-prone requires
org.pcollections:pcollections 4.0.1. module-info.java is not
compiled, so the class files stay at major version 52.

%prep
%autosetup -n pcollections-%{version}
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete
tar -C %{_builddir} -xf %{SOURCE1}
find "%{_builddir}/pcollections-4.0.1" \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
compile_tree() (
	set -eo pipefail
	dir=$1
	ver=$2
	cd "$dir"
	find src/main/java -name '*.java' ! -name 'module-info.java' > sources.list
	test "$(wc -l < sources.list)" -eq 33
	mkdir -p classes
	javac --release 8 -encoding UTF-8 -Xlint:-options -d classes @sources.list
	mkdir -p classes/META-INF/native-image/org.pcollections/pcollections
	/bin/cp -f src/main/resources/META-INF/native-image/org.pcollections/pcollections/native-image.properties \
		classes/META-INF/native-image/org.pcollections/pcollections/
	cat > manifest.mf << 'EOF'
Manifest-Version: 1.0
Automatic-Module-Name: org.pcollections

EOF
	jar cfm pcollections.jar manifest.mf -C classes .
	jar i pcollections.jar
	javap -verbose -cp pcollections.jar org.pcollections.ConsPStack | grep -F -q 'major version: 52'
	if [ "$ver" = "%{version}" ]; then
		javap -cp pcollections.jar org.pcollections.OrderedPSet | grep -F -q 'boolean contains(java.lang.Object)'
		javap -cp pcollections.jar org.pcollections.OrderedPMap | grep -F -q 'boolean containsKey(java.lang.Object)'
	fi
	cat > pcollections.pom << EOF
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.pcollections</groupId>
  <artifactId>pcollections</artifactId>
  <version>${ver}</version>
  <name>PCollections</name>
  <description>Persistent Java collections</description>
  <licenses>
    <license>
      <name>MIT</name>
    </license>
  </licenses>
</project>
EOF
	grep -F -q "<version>${ver}</version>" pcollections.pom
)
compile_tree "%{_builddir}/pcollections-4.0.1" 4.0.1
compile_tree "%{_builddir}/pcollections-%{version}" %{version}

%install
set -eo pipefail
old="%{_builddir}/pcollections-4.0.1"
sysjar install --buildroot %{buildroot} \
	--artifact "${old}/pcollections.pom:${old}/pcollections.jar" \
	--file-name pcollections-4.0.1 \
	--filelist .mfiles-old
index="%{buildroot}/usr/share/sysjar/index/org.pcollections/pcollections.sysjar"
test -f "$index"
/bin/mv "$index" "%{buildroot}/usr/share/sysjar/index/org.pcollections/pcollections-4.0.1.sysjar"
sed -i 's|/usr/share/sysjar/index/org\.pcollections/pcollections\.sysjar|/usr/share/sysjar/index/org.pcollections/pcollections-4.0.1.sysjar|' .mfiles-old
idx="%{buildroot}/usr/share/sysjar/index/org.pcollections/pcollections-4.0.1.sysjar"
grep -F -q '"version": "4.0.1"' "$idx"
grep -F -q '"artifactId": "pcollections"' "$idx"
new="%{_builddir}/pcollections-%{version}"
sysjar install --buildroot %{buildroot} \
	--artifact "${new}/pcollections.pom:${new}/pcollections.jar" \
	--file-name pcollections \
	--filelist .mfiles-new
idxn="%{buildroot}/usr/share/sysjar/index/org.pcollections/pcollections.sysjar"
grep -F -q '"version": "%{version}"' "$idxn"
grep -F -q '"artifactId": "pcollections"' "$idxn"
: > .mfiles
for list in .mfiles-old .mfiles-new
do
	while IFS= read -r line; do
		grep -qxF -- "$line" .mfiles || printf '%%s\n' "$line" >> .mfiles
	done < "$list"
done
grep -F -q '/pcollections.jar' .mfiles
grep -F -q '/pcollections-4.0.1.jar' .mfiles

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
mkdir -p check
cat > check/Smoke.java << 'EOF'
import org.pcollections.ConsPStack;
import org.pcollections.HashPMap;
import org.pcollections.HashTreePMap;
import org.pcollections.OrderedPSet;
public class Smoke {
	public static void main(String[] args) {
		ConsPStack<String> stack = ConsPStack.singleton("gradle");
		HashPMap<String, Integer> map = HashTreePMap.singleton("n", 3);
		OrderedPSet<String> set = OrderedPSet.singleton("a");
		if (stack.size() != 1 || map.get("n") == null || map.get("n") != 3 || !set.contains("a")) {
			throw new RuntimeException(stack + " " + map + " " + set);
		}
		System.out.println("pcollections_ok " + stack.get(0) + " " + map.get("n") + " " + stack.size() + " " + set.contains("a"));
	}
}
EOF
run_check() {
	label=$1
	jar=$2
	test -s "$jar"
	mkdir -p "check/${label}"
	javac --release 8 -encoding UTF-8 -Xlint:-options -cp "$jar" -d "check/${label}" check/Smoke.java
	java -cp "check/${label}:${jar}" Smoke > "check/${label}/out.txt"
	cat "check/${label}/out.txt"
	grep -F -q 'pcollections_ok gradle 3 1 true' "check/${label}/out.txt"
}
run_check new "%{buildroot}%{_javadir}/pcollections.jar"
run_check old "%{buildroot}%{_javadir}/pcollections-4.0.1.jar"

%files -f .mfiles
%doc LICENSE README.md
