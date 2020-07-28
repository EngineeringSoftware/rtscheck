package org.rtstest.maven;

import java.util.List;
import java.util.ArrayList;
import java.util.TreeMap;
import java.util.Arrays;
import java.lang.reflect.Field;

class Test {
    private String mName;

    public Test(String name) {
        this.mName = name;
    }

    @Override
    public String toString() {
        return mName;
    }
}

public class Monitor {

    private static final String OBJECT_STRING = "OBJECT";

    private static List<Object> objects;

    static {
        objects = new ArrayList<Object>();
        // add shutdown hook
        Runtime.getRuntime().addShutdownHook(new Thread() {
                @Override
                public void run() {
                    printAllObjects(objects);
                }
            });
    }

    public static void printAndClean() {
        // get the element for the test method name
        objects.add(new Test(extractTestName()));
    }

    private static String extractTestName() {
        StackTraceElement stackElements[] = Thread.currentThread().getStackTrace();
        for (StackTraceElement ste : stackElements) {
            String name = ste.getClassName();
            if (name.contains(".Test")) {
                return name;
            }
        }
        return "UNK";
    }

    public static void saveClass(String className) {
        // NOT USED: we currently do not invoke this method as we do
        // not expect (at the moment) to have programs with static
        // variables.
    }

    public static void saveObject(Object obj) {
        // WARNING: hard coded packag name.
        if (obj != null &&
                (obj.getClass().getName().startsWith("p.") || obj.getClass().getName().startsWith("Package")) &&
                !objects.contains(obj)) {
            objects.add(obj);
        }
    }

    private static void printAllObjects(List<Object> objects) {
        try {
            for (Object obj : objects) {
                if (obj instanceof Test ) {
                    println("===== " + obj);
                    continue;
                }
                // we want sorted map
                TreeMap<String, String> fldName2fldValue = getAllFieldValues(obj);
                println(OBJECT_STRING + ": #" + fldName2fldValue.size() + " " + fldName2fldValue + " " + getClassHierarchy(obj));
            }
        } catch (Exception ex) {
            ex.printStackTrace();
        }
    }

    // get only primitive fields (also those that are inherited)
    private static TreeMap<String, String> getAllFieldValues(Object obj) throws Exception {
        TreeMap<String, String> fldName2fldValue = new TreeMap<String, String>();

        List<Field> flds = getAllFields(obj);
        for (Field fld : flds) {
            fld.setAccessible(true);
            Class<?> type = fld.getType();

            String name = fld.getName();
            String value = "UNK";

            if (type == boolean.class) {
                value = Boolean.toString(fld.getBoolean(obj));
            } else if (type == byte.class) {
                value = Byte.toString(fld.getByte(obj));
            } else if (type == short.class) {
                value = Short.toString(fld.getShort(obj));
            } else if (type == char.class) {
                value = Character.toString(fld.getChar(obj));
            } else if (type == int.class) {
                value = Integer.toString(fld.getInt(obj));
            } else if (type == long.class) {
                value = Long.toString(fld.getLong(obj));
            } else if (type == float.class) {
                value = Float.toString(fld.getFloat(obj));
            } else if (type == double.class) {
                value = Double.toString(fld.getDouble(obj));
            } else {
                // nothing for now
            }

            value += ":" + type.getName();

            fldName2fldValue.put(name, value);
        }

        return fldName2fldValue;
    }

    private static List<Field> getAllFields(Object obj) {
        return getAllFields(obj.getClass());
    }

    private static List<Field> getAllFields(Class<?> clz) {
        List<Field> flds = new ArrayList<Field>();
        if (clz.getSuperclass() != Object.class) {
            flds.addAll(getAllFields(clz.getSuperclass()));
        }
        flds.addAll(Arrays.asList(clz.getDeclaredFields()));
        return flds;
    }

    private static String getClassHierarchy(Object obj) {
        return getClassHierarchy(obj.getClass());
    }

    private static String getClassHierarchy(Class<?> clz) {
        return clz == null ? "null" : clz.getName() + ":" + getClassHierarchy(clz.getSuperclass());
    }

    private static void println(String msg) {
        System.out.println(msg);
    }
}
