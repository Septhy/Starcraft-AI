package bridge;

import bwapi.BWClient;
import bwapi.DefaultBWListener;
import bwapi.Flag;
import bwapi.Game;
import bwapi.Player;
import bwapi.Position;
import bwapi.Unit;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.Socket;
import java.util.HashMap;
import java.util.Map;

/**
 * The link between StarCraft 1.16.1 and the Python trainer.
 *
 * Every few frames it sends the trainer one line describing the units of
 * both sides, then waits for the trainer's commands and gives them to
 * the units. The game stands still while it waits, so the trainer can
 * take as long as it likes.
 *
 * Sent, one line:
 *   {"frame":N,"own":[[id,x,y,hp,maxhp,visible],...],"enemy":[...]}
 * Received, one command per line, then END:
 *   A id targetId      attack that unit
 *   M id x y           move to that point
 *   RESTART            start the game again
 *   END
 */
public class Bridge extends DefaultBWListener {
    private static final int PORT =
        Integer.parseInt(System.getProperty("scai.port", "11111"));
    private static final int FRAMES_PER_STEP =
        Integer.parseInt(System.getProperty("scai.skip", "8"));
    private static final boolean DRAW =
        !"0".equals(System.getProperty("scai.gui", "1"));

    private BWClient client;
    private Game game;
    private Socket socket;
    private BufferedReader in;
    private PrintWriter out;
    /** The last attack target given to each unit, so it is not repeated. */
    private final Map<Integer, Integer> lastTarget = new HashMap<>();

    public static void main(String[] args) {
        Bridge b = new Bridge();
        b.client = new BWClient(b);
        b.client.startGame();
    }

    private void connect() {
        while (socket == null) {
            try {
                socket = new Socket("127.0.0.1", PORT);
                socket.setTcpNoDelay(true);
                in = new BufferedReader(
                    new InputStreamReader(socket.getInputStream(), "UTF-8"));
                out = new PrintWriter(socket.getOutputStream(), false);
                System.out.println("Connected to the trainer.");
            } catch (IOException e) {
                System.out.println("Waiting for the trainer on port " + PORT
                    + " (start: python -m scai.train --env bwapi)");
                try { Thread.sleep(2000); } catch (InterruptedException x) { }
            }
        }
    }

    @Override
    public void onStart() {
        game = client.getGame();
        // Complete information is used only for keeping score (who died).
        // The brain is shown visible units only: see the "visible" field.
        game.enableFlag(Flag.CompleteMapInformation);
        game.enableFlag(Flag.UserInput);
        game.setLocalSpeed(0);
        game.setGUI(DRAW);
        lastTarget.clear();
        connect();
    }

    private void appendUnits(StringBuilder sb, Player p) {
        sb.append('[');
        boolean first = true;
        for (Unit u : p.getUnits()) {
            if (!u.exists() || !u.isCompleted() || u.getHitPoints() <= 0
                    || u.getType().isBuilding()) {
                continue;
            }
            if (!first) sb.append(',');
            first = false;
            int hp = u.getHitPoints() + u.getShields();
            int max = u.getType().maxHitPoints() + u.getType().maxShields();
            sb.append('[').append(u.getID()).append(',').append(u.getX())
              .append(',').append(u.getY()).append(',').append(hp)
              .append(',').append(max).append(',')
              .append(u.isVisible() ? 1 : 0).append(']');
        }
        sb.append(']');
    }

    @Override
    public void onFrame() {
        if (game.isPaused() || game.getFrameCount() % FRAMES_PER_STEP != 0) {
            return;
        }
        StringBuilder sb = new StringBuilder(512);
        sb.append("{\"frame\":").append(game.getFrameCount())
          .append(",\"own\":");
        appendUnits(sb, game.self());
        sb.append(",\"enemy\":");
        appendUnits(sb, game.enemy());
        sb.append('}');
        try {
            out.println(sb);
            out.flush();
            String line;
            while ((line = in.readLine()) != null && !line.equals("END")) {
                obey(line.trim().split(" "));
            }
            if (line == null) throw new IOException("trainer closed");
        } catch (IOException e) {
            System.out.println("Lost the trainer: " + e.getMessage());
            try { socket.close(); } catch (IOException x) { }
            socket = null;
            connect();
        }
    }

    private void obey(String[] w) {
        if (w[0].equals("RESTART")) {
            game.restartGame();
            return;
        }
        Unit u = game.getUnit(Integer.parseInt(w[1]));
        if (u == null || !u.exists()) return;
        if (w[0].equals("A")) {
            int targetId = Integer.parseInt(w[2]);
            Unit t = game.getUnit(targetId);
            if (t == null || !t.exists()) return;
            // Giving the same attack order again interrupts the shot.
            Integer last = lastTarget.get(u.getID());
            if (last != null && last == targetId) return;
            u.attack(t);
            lastTarget.put(u.getID(), targetId);
        } else if (w[0].equals("M")) {
            u.move(new Position(Integer.parseInt(w[2]),
                                Integer.parseInt(w[3])));
            lastTarget.remove(u.getID());
        }
    }
}
