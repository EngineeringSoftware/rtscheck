package org.rtstest.maven;

import org.rtstest.asm.*;

public class ObjectsCV extends ClassVisitor {

    public ObjectsCV(String className, ClassVisitor cv) {
        super(Opcodes.ASM6, cv);
    }

    @Override
    public MethodVisitor visitMethod(int access,
                                     String name,
                                     String desc,
                                     String signature,
                                     String[] exceptions) {
        MethodVisitor mv = super.visitMethod(access, name, desc, signature, exceptions);
        return new ObjectsMV(name, mv);
    }
}
