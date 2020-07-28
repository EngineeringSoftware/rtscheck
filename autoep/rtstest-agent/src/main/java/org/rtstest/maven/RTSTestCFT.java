package org.rtstest.maven;

import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.lang.instrument.ClassFileTransformer;
import java.net.URL;
import java.security.ProtectionDomain;

import org.rtstest.asm.ClassReader;
import org.rtstest.asm.ClassWriter;

import java.util.regex.Pattern;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.util.Collections;
import java.util.Set;
import java.util.zip.Checksum;
import java.util.zip.Adler32;
import java.util.zip.ZipEntry;
import java.util.zip.ZipException;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;

/**
 * Transformer that instrument classes to collect dependencies.
 */
public final class RTSTestCFT implements ClassFileTransformer {

    public boolean mIsLoaded;

    /**
     * Constructor.
     */
    public RTSTestCFT() {
    }

    @Override
    public byte[] transform(ClassLoader loader, String className, Class<?> classBeingRedefined,
            ProtectionDomain protectionDomain, byte[] classfileBuffer) {

        // Ensure that monitor is accessible from the ClassLoader.
        if (!isMonitorAccessibleFromClassLoader(loader)) {
            return null;
        }

        if (className.contains("$Proxy") ||
                className.startsWith("java/") ||
                className.startsWith("javax/") ||
                className.startsWith("sun/") ||
                className.startsWith("org/apache/") ||
                className.startsWith("org/eclipse/") ||
                className.startsWith("org/rtstest") ||
                className.startsWith("org/junit") ||
                className.startsWith("junit/") ||
                className.startsWith("org/sonatype/")) {
            return null;
        }

        // Save info that class is loaded.
        Monitor.saveClass(className);

        // Instrument class.
        classfileBuffer = instrumentClass(loader, className, classfileBuffer);

        // Line for debugging.
        // saveClassfileBufferForDebugging(className, classfileBuffer);
        return classfileBuffer;
    }

    protected byte[] instrumentClass(ClassLoader loader, String className,
                                     byte[] classfileBuffer) {
        // // Instrument class.
        ClassReader classReader = new ClassReader(classfileBuffer);
        // Removed COMPUTE_FRAMES as I kept seeing linkage error
        // with Java 7. However for our current instrumentation
        // this argument seems not necessary.
        ClassWriter classWriter = new ClassWriter(classReader,
        /* ClassWriter.COMPUTE_FRAMES | */ClassWriter.COMPUTE_MAXS);
        ObjectsCV visitor = new ObjectsCV(className, classWriter);
        // // NOTE: cannot skip debug as some tests depend on these info.
        // classReader.accept(asmClassVisitor, ClassReader.SKIP_DEBUG);
        classReader.accept(visitor, 0);
        byte[] modifiedClassfileBuffer = classWriter.toByteArray();
        classfileBuffer = modifiedClassfileBuffer;
        return classfileBuffer;
    }

    // Check if loader knows about monitors, otherwise do not
    // instrument; TODO: we should log this problem.
    // TODO: Check if this method is needed after introducing
    // LoaderMethodVisitor and LoaderMonitor.
    private boolean isMonitorAccessibleFromClassLoader(ClassLoader loader) {
        if (loader == null) {
            return false;
        }
        boolean isMonitorAccessible = true;
        InputStream monitorInputStream = null;
        try {
            //            monitorInputStream = loader.getResourceAsStream("org/rtstest/maven/Monitor.class");
            //            if (monitorInputStream == null) {
            //                isMonitorAccessible = false;
            //            }
        } catch (Exception ex1) {
            isMonitorAccessible = false;
            try {
                if (monitorInputStream != null) {
                    monitorInputStream.close();
                }
            } catch (IOException ex2) {
                // do nothing
            }
        }
        return isMonitorAccessible;
    }
    
    // DEBUGGING

    /**
     * This method is for debugging purposes. So far one of the best way to
     * debug instrumentation was to actually look at the instrumented code. This
     * method let us choose which class to print.
     * 
     * @param className
     *            Name of the class being instrumented.
     * @param classfileBuffer
     *            Byte array with the instrumented class content.
     */
    @SuppressWarnings("unused")
    private void saveClassfileBufferForDebugging(String className, byte[] classfileBuffer) {
        try {
            if (className.contains("CX")) {
                java.io.DataOutputStream tmpout = new java.io.DataOutputStream(new java.io.FileOutputStream("out"));
                tmpout.write(classfileBuffer, 0, classfileBuffer.length);
                tmpout.close();
            }
        } catch (Exception ex) {
            ex.printStackTrace();
        }
    }

}
