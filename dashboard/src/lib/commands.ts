export interface CommandSyntax {
  title: string;
  desc: string;
  usage: string[];
}

export const COMMAND_SYNTAX: Record<string, CommandSyntax> = {
  ban: {
    title: "Ban Command",
    desc: "Bans a specified member from the server.",
    usage: [
      "• `!ban <member> [reason]` — Ban a user from the guild."
    ]
  },
  unban: {
    title: "Unban Command",
    desc: "Unbans a user using their Discord account ID.",
    usage: [
      "• `!unban <user_id> [reason]` — Unban a user from the guild."
    ]
  },
  kick: {
    title: "Kick Command",
    desc: "Kicks a specified member from the server.",
    usage: [
      "• `!kick <member> [reason]` — Kick a member from the guild."
    ]
  },
  timeout: {
    title: "Timeout Command",
    desc: "Mutes/times out a member for a given duration.",
    usage: [
      "• `!timeout <member> <minutes> [reason]` — Timeout a member (1-40320 mins)."
    ]
  },
  untimeout: {
    title: "Untimeout Command",
    desc: "Removes a timeout from a timed-out member.",
    usage: [
      "• `!untimeout <member> [reason]` — Remove an active timeout."
    ]
  },
  warn: {
    title: "Warn Command",
    desc: "Logs a formal moderation warning for a member.",
    usage: [
      "• `!warn <member> [reason]` — Warn a member in the server."
    ]
  },
  warnings: {
    title: "Warnings Command",
    desc: "Displays all recorded warnings for a member.",
    usage: [
      "• `!warnings <member>` — View warnings for a member."
    ]
  },
  clearwarnings: {
    title: "Clear Warnings Command",
    desc: "Clears all recorded warnings for a member.",
    usage: [
      "• `!clearwarnings <member>` — Clear all warnings for a member."
    ]
  },
  purge: {
    title: "Purge Command",
    desc: "Deletes a specified number of recent messages from the channel.",
    usage: [
      "• `!purge <1-100>` — Purge chat history."
    ]
  },
  embed: {
    title: "Embed Command",
    desc: "Sends a custom formatted embed message.",
    usage: [
      "• `!embed <title> | <description> | [hex_color]` — Send a custom embed."
    ]
  },
  nuke: {
    title: "Nuke Command",
    desc: "Clones and deletes the current channel to wipe chat history.",
    usage: [
      "• `!nuke` — Reset and wipe the current channel."
    ]
  },
  autonuke: {
    title: "Auto-Nuke Commands",
    desc: "Automatically wipe a channel's history on a repeating timer.",
    usage: [
      "• `!autonuke set <minutes>` — Enable auto-nuke for this channel.",
      "• `!autonuke remove` — Disable auto-nuke for this channel."
    ]
  },
  voicemaster: {
    title: "VoiceMaster Commands",
    desc: "Configure the dynamic voice channel and interface panel.",
    usage: [
      "• `!voicemaster setup` — Configure the VoiceMaster category and interface."
    ]
  },
  serverinfo: {
    title: "Server Info Command",
    desc: "Displays detailed statistics about the current server.",
    usage: [
      "• `!serverinfo` — View server statistics."
    ]
  },
  channelinfo: {
    title: "Channel Info Command",
    desc: "Displays information about a text channel.",
    usage: [
      "• `!channelinfo [channel]` — View channel information."
    ]
  },
  userinfo: {
    title: "User Info Command",
    desc: "Displays detailed profile information about a member or yourself.",
    usage: [
      "• `!userinfo [member]` — View user profile details."
    ]
  },
  snipe: {
    title: "Snipe Command",
    desc: "Snipes the most recently deleted message in this channel.",
    usage: [
      "• `!snipe` — Retrieve the last deleted message."
    ]
  },
  editsnipe: {
    title: "Edit Snipe Command",
    desc: "Snipes the pre-edited version of the last modified message.",
    usage: [
      "• `!editsnipe` — Retrieve the last edited message."
    ]
  },
  clearsnipe: {
    title: "Clear Snipe Command",
    desc: "Purges cached deleted and edited messages from this channel.",
    usage: [
      "• `!clearsnipe` — Wipe cached snipes."
    ]
  },
  afk: {
    title: "AFK Command",
    desc: "Sets your status to away from keyboard with an optional reason.",
    usage: [
      "• `!afk [reason]` — Set your AFK message."
    ]
  },
  play: {
    title: "Play Command",
    desc: "Plays audio from YouTube, SoundCloud, Spotify, or Deezer.",
    usage: [
      "• `!play <song name or link>` — Queue a track to stream."
    ]
  },
  playnext: {
    title: "Play Next Command",
    desc: "Inserts a track straight to the very front of the audio queue.",
    usage: [
      "• `!playnext <song name or link>` — Prioritize track next in queue."
    ]
  },
  queue: {
    title: "Queue Command",
    desc: "Displays the list of upcoming tracks.",
    usage: [
      "• `!queue` — View server music queue."
    ]
  },
  volume: {
    title: "Volume Command",
    desc: "Adjusts music playback volume percentage.",
    usage: [
      "• `!volume <1-100>` — Change playback loudness."
    ]
  },
  autoplay: {
    title: "Autoplay Command",
    desc: "Toggles automatic playback of recommended songs when the queue runs out.",
    usage: [
      "• `!autoplay` — Toggle autoplay on or off."
    ]
  },
  lock: {
    title: "Lock Command",
    desc: "Locks the current text channel to prevent members from sending messages.",
    usage: [
      "• `!lock` — Lock the current text channel."
    ]
  },
  unlock: {
    title: "Unlock Command",
    desc: "Unlocks the current text channel to allow members to send messages again.",
    usage: [
      "• `!unlock` — Unlock the current text channel."
    ]
  },
  pause: {
    title: "Pause Command",
    desc: "Pauses the currently playing audio stream.",
    usage: [
      "• `!pause` — Pause current track."
    ]
  },
  resume: {
    title: "Resume Command",
    desc: "Resumes audio playback if currently paused.",
    usage: [
      "• `!resume` — Resume playback."
    ]
  },
  jail: {
    title: "Jail Command",
    desc: "Isolates a member to the jail channel and preserves their existing roles.",
    usage: [
      "• `!jail <member> [reason]` — Send member to jail."
    ]
  },
  unjail: {
    title: "Unjail Command",
    desc: "Restores original roles to a jailed member and releases them.",
    usage: [
      "• `!unjail <member>` — Release member from jail."
    ]
  },
  strip: {
    title: "Strip Command",
    desc: "Strips all custom roles from a user and saves them for quick restoration.",
    usage: [
      "• `!strip <member> [reason]` — Strip all custom roles."
    ]
  },
  restore: {
    title: "Restore Command",
    desc: "Restores previously stripped roles to a member.",
    usage: [
      "• `!restore <member>` — Return stripped roles."
    ]
  },
  hardban: {
    title: "Hardban Command",
    desc: "Bans a user and adds them to a persistent SQLite blacklist.",
    usage: [
      "• `!hardban <user_id> [reason]` — Permanently blacklist and ban a user."
    ]
  },
  tempban: {
    title: "Tempban Command",
    desc: "Temporarily bans a member for a specified duration.",
    usage: [
      "• `!tempban <member> <duration> [reason]` — Tempban a user (e.g., 10m, 1h, 1d)."
    ]
  },
  softban: {
    title: "Softban Command",
    desc: "Bans and immediately unbans a user to delete their message history.",
    usage: [
      "• `!softban <member> [reason]` — Softban a user."
    ]
  },
  fakeperms: {
    title: "Fake Permissions Commands",
    desc: "Grant specific roles permission to use bot commands without admin access.",
    usage: [
      "• `!fakeperms add <@role> <command>` — Grant role permission.",
      "• `!fakeperms remove <@role> <command>` — Revoke role permission.",
      "• `!fakeperms list` — View all fake permission mappings."
    ]
  },
  autoresponder: {
    title: "Autoresponder Commands",
    desc: "Configure custom automated message responses.",
    usage: [
      "• `!ar add <trigger> | <response>` — Create custom trigger.",
      "• `!ar remove <trigger>` — Delete trigger.",
      "• `!ar list` — View all active triggers."
    ]
  },
  avatar: {
    title: "Avatar Command",
    desc: "Displays a member's global profile avatar.",
    usage: [
      "• `!avatar [member]` — View avatar."
    ]
  },
  banner: {
    title: "Banner Command",
    desc: "Displays a user's custom profile banner.",
    usage: [
      "• `!banner [user]` — View profile banner."
    ]
  },
  firstmessage: {
    title: "First Message Command",
    desc: "Finds and links to the very first message sent in this channel.",
    usage: [
      "• `!firstmessage` — Get link to first message."
    ]
  },
  mediaonly: {
    title: "Media Only Command",
    desc: "Enforces media-only attachments in a text channel.",
    usage: [
      "• `!mediaonly` — Toggle media enforcement for this channel."
    ]
  },
  role: {
    title: "Role Command",
    desc: "Toggles or grants a role to a member.",
    usage: [
      "• `!role <member> <role>` — Add or remove a role."
    ]
  },
  membercount: {
    title: "Member Count Command",
    desc: "Displays clean server member count statistics.",
    usage: [
      "• `!membercount` — View server counts."
    ]
  },
  prefix: {
    title: "Prefix Command",
    desc: "View or change the command prefix for this server.",
    usage: [
      "• `!prefix` — View the current prefix.",
      "• `!prefix view` — View the current prefix.",
      "• `!prefix set <new_prefix>` — Set a new prefix.",
      "• `!prefix remove` — Reset prefix to default (`!`).",
      "• `!prefix self` — View the prefix the bot is currently responding to."
    ]
  }
};