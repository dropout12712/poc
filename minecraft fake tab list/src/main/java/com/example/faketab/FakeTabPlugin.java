package com.example.faketab;

import com.comphenix.protocol.PacketType;
import com.comphenix.protocol.ProtocolLibrary;
import com.comphenix.protocol.ProtocolManager;
import com.comphenix.protocol.events.PacketContainer;
import com.comphenix.protocol.wrappers.EnumWrappers;
import com.comphenix.protocol.wrappers.PlayerInfoData;
import com.comphenix.protocol.wrappers.WrappedGameProfile;
import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;
import org.bukkit.plugin.java.JavaPlugin;
import org.jetbrains.annotations.NotNull;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

public final class FakeTabPlugin extends JavaPlugin implements CommandExecutor {

    private ProtocolManager protocolManager;
    // Using a ConcurrentHashMap is good practice in case of future async operations
    private final Map<String, WrappedGameProfile> fakePlayers = new ConcurrentHashMap<>();

    @Override
    public void onEnable() {
        // Initialize ProtocolLib's manager
        this.protocolManager = ProtocolLibrary.getProtocolManager();

        // Register the command executor
        Objects.requireNonNull(getCommand("faketab"), "Command 'faketab' is not defined in plugin.yml")
                .setExecutor(this);

        getLogger().info("FakeTabPlugin has been enabled.");
    }

    @Override
    public void onDisable() {
        // When the plugin is disabled, remove all fake players from the tab list
        if (!fakePlayers.isEmpty()) {
            getLogger().info("Clearing " + fakePlayers.size() + " fake players from the tab list...");
            clearAllFakePlayers();
        }
        getLogger().info("FakeTabPlugin has been disabled.");
    }

    @Override
    public boolean onCommand(@NotNull CommandSender sender, @NotNull Command command, @NotNull String label, @NotNull String[] args) {
        if (!sender.hasPermission("faketab.admin")) {
            sender.sendMessage(ChatColor.RED + "You do not have permission to use this command.");
            return true;
        }

        if (args.length == 0) {
            sender.sendMessage(ChatColor.RED + "Usage: /" + label + " <add|addbulk|remove|clear> [name/amount]");
            return true;
        }

        String subCommand = args[0].toLowerCase();
        switch (subCommand) {
            case "add" -> handleAdd(sender, args);
            case "addbulk" -> handleAddBulk(sender, args);
            case "remove" -> handleRemove(sender, args);
            case "clear" -> handleClear(sender);
            default -> sender.sendMessage(ChatColor.RED + "Unknown subcommand. Usage: /" + label + " <add|addbulk|remove|clear>");
        }
        return true;
    }

    // --- Command Logic Methods ---

    private void handleAdd(CommandSender sender, String[] args) {
        if (args.length < 2) {
            sender.sendMessage(ChatColor.RED + "Usage: /faketab add <name>");
            return;
        }
        String name = args[1];
        if (fakePlayers.containsKey(name.toLowerCase())) {
            sender.sendMessage(ChatColor.RED + "A fake player with that name already exists.");
            return;
        }

        WrappedGameProfile profile = new WrappedGameProfile(UUID.randomUUID(), name);
        fakePlayers.put(name.toLowerCase(), profile);
        addFakePlayerPacket(profile);
        sender.sendMessage(ChatColor.GREEN + "Added fake player '" + name + "' to the tab list.");
    }

    private void handleAddBulk(CommandSender sender, String[] args) {
        if (args.length < 2) {
            sender.sendMessage(ChatColor.RED + "Usage: /faketab addbulk <amount>");
            return;
        }

        int amount;
        try {
            amount = Integer.parseInt(args[1]);
            if (amount <= 0 || amount > 200) { // Safety cap to prevent client crashes
                sender.sendMessage(ChatColor.RED + "Please enter a number between 1 and 200.");
                return;
            }
        } catch (NumberFormatException e) {
            sender.sendMessage(ChatColor.RED + "'" + args[1] + "' is not a valid number.");
            return;
        }

        for (int i = 0; i < amount; i++) {
            // Generate a unique name
            String name = "StressTest_" + UUID.randomUUID().toString().substring(0, 8);
            WrappedGameProfile profile = new WrappedGameProfile(UUID.randomUUID(), name);
            fakePlayers.put(name.toLowerCase(), profile);
            addFakePlayerPacket(profile);
        }
        sender.sendMessage(ChatColor.GREEN + "Added " + amount + " fake players.");
    }


    private void handleRemove(CommandSender sender, String[] args) {
        if (args.length < 2) {
            sender.sendMessage(ChatColor.RED + "Usage: /faketab remove <name>");
            return;
        }
        String name = args[1].toLowerCase();
        WrappedGameProfile profile = fakePlayers.remove(name);
        if (profile == null) {
            sender.sendMessage(ChatColor.RED + "No fake player with that name was found.");
            return;
        }

        removeFakePlayerPacket(profile);
        sender.sendMessage(ChatColor.GREEN + "Removed fake player '" + args[1] + "'.");
    }

    private void handleClear(CommandSender sender) {
        if (fakePlayers.isEmpty()) {
            sender.sendMessage(ChatColor.YELLOW + "There are no fake players to clear.");
            return;
        }
        int count = fakePlayers.size();
        clearAllFakePlayers();
        sender.sendMessage(ChatColor.GREEN + "Successfully cleared all " + count + " fake players.");
    }

    // --- Packet Manipulation Methods ---

    private void addFakePlayerPacket(WrappedGameProfile profile) {
        PacketContainer packet = protocolManager.createPacket(PacketType.Play.Server.PLAYER_INFO_UPDATE);
        packet.getPlayerInfoActions().write(0, EnumSet.of(EnumWrappers.PlayerInfoAction.ADD_PLAYER));

        PlayerInfoData data = new PlayerInfoData(
                profile.getUUID(), 0, false, null, profile, null, null
        );
        packet.getPlayerInfoDataLists().write(0, List.of(data));
        broadcastPacket(packet);
    }

    private void removeFakePlayerPacket(WrappedGameProfile profile) {
        PacketContainer packet = protocolManager.createPacket(PacketType.Play.Server.PLAYER_INFO_REMOVE);
        packet.getUUIDLists().write(0, List.of(profile.getUUID()));
        broadcastPacket(packet);
    }

    private void clearAllFakePlayers() {
        if (fakePlayers.isEmpty()) return;
        PacketContainer packet = protocolManager.createPacket(PacketType.Play.Server.PLAYER_INFO_REMOVE);
        List<UUID> uuids = fakePlayers.values().stream().map(WrappedGameProfile::getUUID).toList();
        packet.getUUIDLists().write(0, uuids);
        broadcastPacket(packet);
        fakePlayers.clear();
    }

    private void broadcastPacket(PacketContainer packet) {
        for (Player player : Bukkit.getOnlinePlayers()) {
            protocolManager.sendServerPacket(player, packet);
        }
    }
}