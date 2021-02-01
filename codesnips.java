package com.threerings.projectx.dungeon.data;

import com.threerings.export.b$g;

public static class Constant extends GateSummary.Wheel
{
    protected byte _skip;
    protected GateSummary.Wedge[] _wedges;
    protected float _velocity;
    protected float[] _lengths;
    protected long _start;
    
    public Constant(final byte skip, final GateSummary.Wedge[] wedges, final float velocity, final float[] lengths, final long start) {
        this._skip = skip;
		this._wedges = wedges;
        this._velocity = velocity;
        this._lengths = lengths;
        this._start = start;
    }
    
    public Constant() {
    }
    
    public final int Fd() {
        return this._skip;
    }
    
    public final boolean Fe() {
        GateSummary.Wedge[] wedges;
        for (int length = (wedges = this._wedges).length, i = 0; i < length; ++i) {
            if (wedges[i].isTier()) {
                return true;
            }
        }
        return false;
    }
    
    public final GateSummary.Wedge[] Ff() {
        return this._wedges;
    }
    
    public final int a(final float n, final long n2) {
        return this.ag(this.c(n, n2));
    }
    
    public final int ag(final float n) {
        final float[] lengths = this._lengths;
        float m = clampPositiveTwoPi(n);
        for (int i = 0; i < lengths.length; ++i) {
            if ((m -= lengths[i]) < 0.0f) {
                return i;
            }
        }
        return lengths.length - 1;
    }
    
    public final int b(final float n, final long n2) {
        return this.ah(this.c(0.0f, n2));
    }
    
    public final int ah(final float n) {
        final float[] lengths = this._lengths;
        float n2;
        if ((n2 = clampPositiveTwoPi(n) - lengths[0] / 2.0f) < 0.0f) {
            return lengths.length - 1;
        }
        for (int i = 0; i < lengths.length; ++i) {
            if ((n2 -= lengths[i] / 2.0f + lengths[(i + 1) % lengths.length] / 2.0f) < 0.0f) {
                return i;
            }
        }
        return lengths.length - 1;
    }
    
    public final float e(final int n, final long n2) {
        return clampCenteredTwoPi(this.getDistanceTraveled(n2) + this.getOffset(n));
    }
    
	// cL()
    public final float getOffset(final int n) {
        final float[] lengths = this._lengths;
        float n2 = 0.0f;
        for (int i = 0; i < n; ++i) {
            n2 += lengths[i];
        }
        return clampCenteredTwoPi(n2 + lengths[n] * 0.5f);
    }
    
    private float c(final float n, final long n2) {
        return clampCenteredTwoPi(n - this.getDistanceTraveled(n2));
    }
    
	// Z()
    public final float getDistanceTraveled(final long n) {
        final float velocity = this._velocity;
        final long start = this._start;
        final float n2 = velocity;
        final float abs;
        if ((abs = Math.abs(velocity)) < 1.0E-6f) {
            return 0.0f;
        }
        return clampCenteredTwoPi((n - start) % (long)(6283.1855f / abs) * n2 / 1000.0f);
    }
    
    public final int getDirection() {
        return (int)Math.signum(this._velocity);
    }
}