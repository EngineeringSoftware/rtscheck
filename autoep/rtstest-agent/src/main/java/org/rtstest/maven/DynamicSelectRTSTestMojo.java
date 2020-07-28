package org.rtstest.maven;

import java.io.File;
import java.io.IOException;
import java.net.JarURLConnection;
import java.net.URL;

import org.apache.maven.plugin.MojoExecutionException;
import org.apache.maven.plugins.annotations.LifecyclePhase;
import org.apache.maven.plugins.annotations.Mojo;

import org.rtstest.maven.AgentLoader;

@Mojo(name = "select", defaultPhase = LifecyclePhase.PROCESS_TEST_CLASSES)
public class DynamicSelectRTSTestMojo extends AbstractRTSTestMojo {

    public void execute() throws MojoExecutionException {
        if (getSkip()) {
            getLog().info("RTSTest is skipped.");
            return;
        }
        if (getSkipTests()) {
            getLog().info("Tests are skipped.");
            return;
        }
        executeThis();
    }

    // INTERNAL

    /**
     * Implements 'select' that does not require changes to any
     * existing plugin in configuration file(s).
     */
    private void executeThis() throws MojoExecutionException {
        // Try to attach agent that will modify Surefire.
        //if (AgentLoader.loadRtstestAgent()) {
        try {
            //ClassLoader.getSystemClassLoader().loadClass("org.rtstest.maven.Monitor");
            URL agentJarURL = extractJarURL(RTSTestAgent.class);
            String agentAbsolutePath = new File(agentJarURL.toURI().getSchemeSpecificPart()).getAbsolutePath();
            String more = "-javaagent:" + agentAbsolutePath;
            String argLine = System.getProperty("argLine");
            more += argLine == null ? "" : argLine;
            System.setProperty("argLine", more);
        } catch (Exception ex) {
            throw new MojoExecutionException("Rtstest cannot attach to the JVM, please specify Rtstest 'restore' explicitly.");
        }
        //        } else {
        //            throw new MojoExecutionException("Rtstest cannot attach to the JVM, please specify Rtstest 'restore' explicitly.");
        //        }
    }

    public static URL extractJarURL(URL url) throws IOException {
        JarURLConnection connection = (JarURLConnection) url.openConnection();
        return connection.getJarFileURL();
    }

    /**
     * Extract URL part that corresponds to jar portion of url for the given
     * class.
     */
    public static URL extractJarURL(Class<?> clz) throws IOException {
        return extractJarURL(getResource(clz));
    }

    public static URL getResource(Class<?> clz) {
        return clz.getResource("/" + clz.getName().replace('.', '/') + ".class");
    }
}
