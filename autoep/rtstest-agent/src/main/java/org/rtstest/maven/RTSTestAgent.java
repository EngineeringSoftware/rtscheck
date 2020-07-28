package org.rtstest.maven;

import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.Instrumentation;
import java.lang.instrument.UnmodifiableClassException;
import java.util.Iterator;
import java.util.Set;

public class RTSTestAgent {

    /** Name of the Agent */
    private static Instrumentation sInstrumentation;

    public static void premain(String options, Instrumentation instrumentation) {
        init(instrumentation);
    }

    public static void agentmain(String options, Instrumentation instrumentation) {
        init(instrumentation);
    }

    public static Instrumentation getInstrumentation() {
        return sInstrumentation;
    }

    private static void init(Instrumentation instrumentation) {
        if (sInstrumentation == null) {
            sInstrumentation = instrumentation;
            instrumentation.addTransformer(new RTSTestCFT(), true);
            // reinstrument(instrumentation);
        }
    }

    private static void reinstrument(Instrumentation instrumentation) {
        try {
            for (Class<?> clz : instrumentation.getAllLoadedClasses()) {
                String name = clz.getName();
                instrumentation.retransformClasses(clz);
            }
        } catch (UnmodifiableClassException ex) {
            // Consider something better than doing nothing.
        }
    }
}
