import { CommandSystem, CommandSystemDonate, CommandSystemExit, isCommandSystemDonate, isCommandSystemExit } from './framework/types/commands';
import { Bridge } from './framework/types/modules';

export default class FakeBridge implements Bridge {
  send(command: CommandSystem): void {
    if (isCommandSystemDonate(command)) {
      this.handleDonation(command);
    } else if (isCommandSystemExit(command)) {
      this.handleExit(command);
    } else {
      console.log('[FakeBridge] received unknown command: ' + JSON.stringify(command));
    }
  }

  async handleDonation(command: CommandSystemDonate): Promise<void> {
    console.log(`[FakeBridge] received donation: ${command.key}=${command.json_string}`);

    // Send data to backend server
    try {
      const response = await fetch('http://localhost:4000/donate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: command.json_string, // Assuming this is a JSON string
      });

      if (response.ok) {
        console.log('[FakeBridge] Data sent to backend successfully');
      } else {
        console.error('[FakeBridge] Failed to send data to backend:', response.statusText);
      }
    } catch (error) {
      console.error('[FakeBridge] Error sending data to backend:', error);
    }
  }

  handleExit(command: CommandSystemExit): void {
    console.log(`[FakeBridge] received exit: ${command.code}=${command.info}`);
  }
}
