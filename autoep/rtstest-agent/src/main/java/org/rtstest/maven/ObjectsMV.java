package org.rtstest.maven;

import org.rtstest.asm.*;

public class ObjectsMV extends MethodVisitor {

    private String mMethodName;

    private boolean mIsConstructor;

    public ObjectsMV(String methodName, MethodVisitor mv) {
        super(Opcodes.ASM6, mv);
        this.mMethodName = methodName;
        this.mIsConstructor = methodName.equals("<init>");
    }

    @Override
    public void visitCode() {
        super.visitCode();
    }

    @Override
    public void visitInsn(int opcode) {
        if (mIsConstructor && opcode == Opcodes.RETURN) {
            mv.visitVarInsn(Opcodes.ALOAD, 0);
            mv.visitMethodInsn(Opcodes.INVOKESTATIC, "org/rtstest/maven/Monitor", "saveObject", "(Ljava/lang/Object;)V", false);
        }
        super.visitInsn(opcode);
    }
}
