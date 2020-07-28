package org.rtstest.maven;

import org.apache.maven.plugin.AbstractMojo;
import org.apache.maven.plugin.MojoExecutionException;

import org.apache.maven.plugins.annotations.Parameter;

import java.io.File;

import org.apache.maven.project.MavenProject;
import org.apache.maven.model.PluginExecution;
import org.apache.maven.model.Plugin;

public abstract class AbstractRTSTestMojo extends AbstractMojo {

    /** Name of property that is used by surefireplugin to set JVM arguments */
    protected static final String ARG_LINE_PARAM_NAME = "argLine";

    @Parameter(property="project")
    protected MavenProject project;

    @Parameter(defaultValue = "${project.build.directory}")
    protected String projectBuildDir;

    @Parameter(defaultValue = "${basedir}")
    protected File basedir;

    /**
     * Clone of "skipTests" in surefire.  Rtstest is not executed if
     * this flag is true.  This property should not be set only for
     * Rtstest configuration.
     */
    @Parameter(property = "skipTests", defaultValue = "false")
    private boolean skipTests;

    /**
     * If set to true, skip using Rtstest.
     *
     * @since 4.1.0
     */
    @Parameter(property = "rtstest.skip", defaultValue = "false")
    private boolean skipme;

    /**
     * Parent of .rtstest directory.
     *
     * @since 4.5.0
     */
    @Parameter(property = "rtstest.parentdir", defaultValue = "${basedir}")
    protected File parentdir;

    public boolean getSkipTests() {
        return skipTests;
    }

    public boolean getSkip() {
        return skipme;
    }

    public File getParentdir() {
        return parentdir;
    }
}
