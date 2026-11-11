Name:		pcollections
Version:	4.0.1
Release:	1
Summary:	Persistent Java collections
Group:		Development/Java
License:	MIT
URL:		https://github.com/hrldcpr/pcollections
# Tag v4.0.1. The Gradle wrapper jar is not in this archive.
Source0:	https://github.com/hrldcpr/pcollections/archive/refs/tags/v%{version}.tar.gz#/pcollections-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem

%description
PCollections %{version} is a library of persistent and immutable
collection classes. Error Prone 2.50.0 links this jar. module-info.java
is not compiled, so the class files stay readable on JDK 25.

%prep
%autosetup -n pcollections-%{version}
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete

%build
set -eo pipefail
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
javap -verbose -cp pcollections.jar org.pcollections.ConsPStack | grep -F 'major version: 52'

cat > pcollections.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.pcollections</groupId>
  <artifactId>pcollections</artifactId>
  <version>4.0.1</version>
  <name>PCollections</name>
  <description>Persistent Java collections</description>
  <licenses>
    <license>
      <name>MIT</name>
    </license>
  </licenses>
</project>
EOF

%install
sysjar install --buildroot %{buildroot} \
	--artifact pcollections.pom:pcollections.jar \
	--file-name pcollections \
	--filelist .mfiles

%check
set -eo pipefail
mkdir -p check
cat > check/Smoke.java << 'EOF'
import org.pcollections.ConsPStack;
import org.pcollections.HashPMap;
import org.pcollections.HashTreePMap;
public class Smoke {
	public static void main(String[] args) {
		ConsPStack<String> stack = ConsPStack.singleton("gradle");
		HashPMap<String, Integer> map = HashTreePMap.singleton("n", 3);
		if (stack.size() != 1 || map.get("n") == null || map.get("n") != 3) {
			throw new RuntimeException(stack + " " + map);
		}
		System.out.println("pcollections_ok " + stack.get(0) + " " + map.get("n") + " " + stack.size());
	}
}
EOF
JAR=%{buildroot}%{_javadir}/pcollections.jar
test -f "$JAR"
javac --release 8 -encoding UTF-8 -Xlint:-options -cp "$JAR" -d check check/Smoke.java
java -cp "check:$JAR" Smoke > check/out.txt
cat check/out.txt
grep -F -q 'pcollections_ok gradle 3 1' check/out.txt

%files -f .mfiles
%doc LICENSE README.md
