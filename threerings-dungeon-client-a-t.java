package com.threerings.projectx.dungeon.client.a;

import com.threerings.opengl.model.a;
import com.threerings.config.ConfigManager;
import com.google.common.base.x;
import com.threerings.projectx.town.data.TownSummary;
import com.threerings.projectx.dungeon.config.DungeonActorConfig;
import com.threerings.tudey.config.ActorConfig;
import com.threerings.config.ArgumentMap;
import com.threerings.tudey.config.PlaceableConfig;
import com.threerings.projectx.dungeon.config.DungeonPlaceableConfig;
import com.threerings.expr.am;
import com.threerings.opengl.renderer.config.ColorizationConfig;
import com.threerings.expr.p;
import com.threerings.opengl.model.config.ModelConfig;
import com.threerings.config.ConfigReference;
import com.threerings.projectx.dungeon.data.GateSummary;
import com.threerings.projectx.dungeon.data.LevelPartyObject;
import com.threerings.projectx.util.A;
import com.threerings.tudey.a.k;
import com.threerings.tudey.a.b.m;

public final class t extends m.e implements k.b
{
    private A afY;
    private LevelPartyObject levelParty;
    private GateSummary gateSummary1;
    private int currentFloor;
    private GateSummary gateSummary2;
    private int nextFloor;
    private ConfigReference<ModelConfig> aBQ;
    private String aBR;
    @p
    protected k _view;
    private static ColorizationConfig[] aBS;
    
    public t(final com.threerings.tudey.util.m m, final am am, final DungeonPlaceableConfig.ElevatorProp elevatorProp) {
        super(m, am);
        this.aBQ = (ConfigReference<ModelConfig>)elevatorProp.model.gV();
        if (m instanceof A) {
            this.afY = (A)m;
            this.levelParty = (LevelPartyObject)this.afY.xk().aW((Class)LevelPartyObject.class);
            if (this.levelParty != null) {
                this.afY.xo();
                this.gateSummary1 = (GateSummary)this.afY.xn().gates.f((Comparable)this.levelParty.gateId);
                this.currentFloor = this.levelParty.floor;
                final ArgumentMap gu;
                if ((gu = elevatorProp.actor.gU()).containsKey((Object)"Push Gate")) {
                    this.gateSummary2 = this.afY.xn().cM("m." + (String)gu.get((Object)"Push Gate"));
                    this.nextFloor = (int)gu.get((Object)"New Floor");
                }
                else if (gu.containsKey((Object)"Return Floor")) {
                    this.gateSummary2 = (GateSummary)this.afY.xn().gates.f((Comparable)this.levelParty.gateId);
                    this.nextFloor = (int)gu.get((Object)"Return Floor");
                }
                else {
                    this.gateSummary2 = (GateSummary)this.afY.xn().gates.f((Comparable)this.levelParty.actualGateId);
                    this.nextFloor = this.levelParty.actualFloor + 1;
                }
                if (this.gateSummary2 != null) {
                    this._view.a((k.b)this);
                }
            }
        }
        this.a((PlaceableConfig.Original)elevatorProp);
    }
    
    public final void dispose() {
        super.dispose();
        if (this.gateSummary2 != null) {
            this._view.b((k.b)this);
        }
    }
    
    public final boolean ca(int i) {
        final ConfigManager configManager;
        final ActorConfig actorConfig;
        final DungeonActorConfig.Elevator elevator = ((actorConfig = (ActorConfig)(configManager = this.aqz.getConfigManager()).a((Class)ActorConfig.class, ((DungeonPlaceableConfig.ElevatorProp)this.aZZ).actor)) == null) ? null : ((DungeonActorConfig.Elevator)actorConfig.ak(configManager));
        final ArgumentMap gu;
        String s = (String)(gu = this.aBQ.gU()).get((Object)"Icon");
        final long xo = this.afY.xo();
        ColorizationConfig[] array = (ColorizationConfig[])gu.get((Object)"Colorizations");
        if (elevator != null) {
            if (~elevator.dissolveParty && this.nextFloor < this.gateSummary2.EZ().length) {
                final GateSummary.Wheel wheel;
				wheel = this.gateSummary2.EZ()[this.nextFloor];
                if (wheel instanceof GateSummary.Random) {
                    s = "ui/icon/map/unknown.png";
                    array = t.aBS;
                }
                else {
					if (this.currentFloor < this.gateSummary1.EZ().length) {
						arg1 = this.gateSummary1.EZ()[this.currentFloor].e(this.levelParty.wedgeIndices[this.currentFloor], xo);
					} else {
						arg1 = 0.0f;
					}
                    i = wheel.a(arg1, xo);
                    final GateSummary.Wedge wedge = this.gateSummary2.EZ()[this.nextFloor].Ff()[i];
                    final StringBuilder append = new StringBuilder().append("ui/icon/map/");
                    // final GateSummary.Wedge wedge2 = wedge;
                    this.afY.xn();
                    s = append.append(wedge.Fb()).append(".png").toString();
                    // final GateSummary.Wedge wedge3 = wedge;
                    this.afY.xn();
                    array = wedge.Fc();
                }
            }
            else {
                i = this.gateSummary1.EX();
                TownSummary homeTown;
                if ((homeTown = (TownSummary)this.afY.xn().towns.f((Comparable)i)) == null) {
                    homeTown = this.afY.uk().homeTown;
                }
                if (homeTown != null) {
                    s = "ui/icon/map/" + homeTown.icon + ".png";
                    array = homeTown.colorizations;
                }
            }
        }
        i = 0;
        if (!x.d((Object)s, gu.get((Object)"Icon")) || array != gu.get((Object)"Colorizations")) {
            gu.put("Icon", (Object)s);
            gu.put("Colorizations", (Object)array);
            i = 1;
        }
        if (i != 0) {
            this._model.setConfig((ConfigReference)this.aBQ);
        }
        if (this.levelParty.aDg != this.aBR) {
            this.aBR = this.levelParty.aDg;
            final a animation;
            if ((animation = this._model.createAnimation(this.aBR)) != null) {
                animation.start();
            }
        }
        return true;
    }
    
    protected final ConfigReference<ModelConfig> b(final PlaceableConfig.Original original) {
        return this.aBQ;
    }
    
    static {
        t.aBS = new ColorizationConfig[] { (ColorizationConfig)ColorizationConfig.createConfig(2, 0.0f, -1.0f, -0.9f), (ColorizationConfig)ColorizationConfig.createConfig(3, 0.0f, -1.0f, -0.35f) };
    }
}