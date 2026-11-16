package lanmc.reclamation.multiplayer.mixin;

import net.minecraft.client.Options;
import net.minecraft.client.gui.screens.TitleScreen;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.objectweb.asm.Opcodes;

@Mixin(value = TitleScreen.class, remap = false)
abstract class TitleScreenMixin {
    // Forge 47.4.0 / Minecraft 1.20.1 production names. The button still uses
    // the stock account gate and opens the normal multiplayer screen.
    @Redirect(
        method = "m_279796_(Lnet/minecraft/client/gui/components/Button;)V",
        at = @At(value = "FIELD", target = "Lnet/minecraft/client/Options;f_92083_:Z",
                 opcode = Opcodes.GETFIELD),
        require = 1, allow = 1, remap = false
    )
    private boolean reclamationSkipThirdPartyNotice(Options options) {
        return true;
    }
}
