#!/bin/bash
### This script integrates RTS tools in pom.xml

_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

# ----------
# Globals.
_Clover__PROFILE=$(cat <<EOF
        <profile>
          <id>cloverp</id>
          <dependencies>
            <dependency>
              <groupId>org.openclover</groupId>
              <artifactId>clover-maven-plugin</artifactId>
              <version>4.2.0</version>
            </dependency>
          </dependencies>
          <build>
            <plugins>
              <plugin>
                <groupId>org.openclover</groupId>
                <artifactId>clover-maven-plugin</artifactId>
                <version>4.2.0</version>
                <executions>
                  <execution>
                    <goals>
                      <goal>setup</goal>
                      <goal>optimize</goal>
                      <goal>snapshot</goal>
                    </goals>
                  </execution>
                </executions>
              </plugin>
              <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>2.19</version>
              </plugin>
            </plugins>
          </build>
        </profile>
EOF
)
_Clover__PROFILE=$(echo ${_Clover__PROFILE} | sed 's/ //g')
_Starts__PROFILE=$(cat <<EOF
        <profile>
          <id>startsp</id>
          <activation>
            <property>
              <name>starts</name>
            </property>
          </activation>
          <build>
            <plugins>
              <plugin>
                <groupId>edu.illinois</groupId>
                <artifactId>starts-maven-plugin</artifactId>
                <version>1.3</version>
              </plugin>
              <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>2.19</version>
              </plugin>
            </plugins>
          </build>
        </profile>
EOF
)
_Starts__PROFILE=$(echo ${_Starts__PROFILE} | sed 's/ //g')
_Ekstazi__PROFILE=$(cat <<EOF
        <profile>
            <id>ekstazip</id>
            <activation>
                <property>
                    <name>ekstazi</name>
                </property>
            </activation>
            <build>
                <plugins>
                  <plugin>
                      <groupId>org.ekstazi</groupId>
                      <artifactId>ekstazi-maven-plugin</artifactId>
                      <version>5.1.0</version>
                      <executions>
                          <execution>
                              <id>ekstazi</id>
                              <goals>
                                  <goal>select</goal>
                              </goals>
                          </execution>
                      </executions>
                  </plugin>
                  <plugin>
                    <groupId>org.apache.maven.plugins</groupId>
                    <artifactId>maven-surefire-plugin</artifactId>
                    <version>2.19</version>
                  </plugin>
                  <!-- EKSTAZI -->
                </plugins>
            </build>
        </profile>
EOF
)
_Ekstazi__PROFILE=$(echo ${_Ekstazi__PROFILE} | sed 's/ //g')
_Notool__PROFILE=$(cat <<EOF
        <profile>
            <id>notoolp</id>
            <build>
                <plugins>
                  <plugin>
                    <groupId>org.apache.maven.plugins</groupId>
                    <artifactId>maven-surefire-plugin</artifactId>
                    <version>2.19</version>
                  </plugin>
                </plugins>
            </build>
        </profile>
EOF
)
_Notool__PROFILE=$(echo ${_Notool__PROFILE} | sed 's/ //g')

function integrate() {
        repo="${1}"; shift
        tool="${1}"; shift

        if [ $tool == 'notool' ]; then
            profile=$_Notool__PROFILE
        elif [ $tool == 'ekstazi' ]; then
            profile=$_Ekstazi__PROFILE
        elif [ $tool == 'clover' ]; then
            profile=$_Clover__PROFILE
        elif [ $tool == 'starts' ]; then
            profile=$_Starts__PROFILE
        fi

        ( cd ${repo};
                for pom in $(find -name "pom*.xml"); do
                        local has_profiles=$( grep 'profiles' ${pom} | wc -l )
                        if [ ${has_profiles} -eq 0 ]; then
                                sed -i 'sX</project>X<profiles>'${profile}'</profiles></project>Xg' ${pom}
                        else
                                sed -i 'sX</profiles>X'${profile}'</profiles>Xg' ${pom}
                        fi
                done
        )
}


#--- Main
integrate "$@"
