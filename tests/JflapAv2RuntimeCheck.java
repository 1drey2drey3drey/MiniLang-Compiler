import automata.Automaton;
import automata.Configuration;
import automata.State;
import automata.Transition;
import automata.pda.CharacterStack;
import automata.pda.PDAConfiguration;
import automata.pda.PDANondeterminismDetector;
import automata.pda.PDATransition;
import automata.pda.PushdownAutomaton;
import automata.turing.TMConfiguration;
import automata.turing.TMSimulator;
import automata.turing.TuringMachine;
import file.XMLCodec;
import file.xml.TMTransducer;
import grammar.Grammar;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Collections;
import java.util.HashSet;
import java.util.Set;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Document;

/**
 * Valida glc.jff, ap.jff e all.jff diretamente com o leitor XMLCodec e os objetos/simuladores
 * oficiais do JFLAP 7.1 (modo headless).
 */
public class JflapAv2RuntimeCheck {

    /**
     * Simula um PushdownAutomaton carregado pelo XMLCodec do JFLAP 7.1 usando
     * CharacterStack, PDATransition e PDAConfiguration reais do JFLAP (aceitação por estado final),
     * sem disparar o JOptionPane modal do construtor do PDAStepByStateSimulator.
     */
    private static boolean simulateJflapPdaByFinalState(PushdownAutomaton pda, String input) {
        State initial = pda.getInitialState();
        CharacterStack initStack = new CharacterStack();
        initStack.push("Z");

        ArrayDeque<PDAConfiguration> queue = new ArrayDeque<>();
        Set<String> visited = new HashSet<>();
        PDAConfiguration start = new PDAConfiguration(initial, null, input, input, initStack, 1);
        queue.add(start);
        visited.add(initial.getID() + "|" + input + "|" + initStack.toString());

        int steps = 0;
        while (!queue.isEmpty() && steps < 50000) {
            steps++;
            PDAConfiguration cur = queue.poll();
            State st = cur.getCurrentState();
            String rem = cur.getUnprocessedInput();
            CharacterStack stack = cur.getStack();

            if (rem.isEmpty() && pda.isFinalState(st)) {
                return true;
            }

            Transition[] transitions = pda.getTransitionsFromState(st);
            for (Transition t : transitions) {
                PDATransition pt = (PDATransition) t;
                String toRead = pt.getInputToRead();
                String toPop = pt.getStringToPop();
                String toPush = pt.getStringToPush();

                if (!rem.startsWith(toRead)) {
                    continue;
                }
                CharacterStack nextStack = new CharacterStack(stack);
                String popped = nextStack.pop(toPop.length());
                if (!popped.equals(toPop)) {
                    continue;
                }
                nextStack.push(toPush);
                String nextRem = rem.substring(toRead.length());
                State nextState = pt.getToState();
                String key = nextState.getID() + "|" + nextRem + "|" + nextStack.toString();
                if (visited.add(key)) {
                    queue.add(new PDAConfiguration(nextState, cur, input, nextRem, nextStack, 1));
                }
            }
        }
        return false;
    }

    public static void main(String[] args) throws Exception {
        java.io.PrintStream report = System.out;
        System.setOut(new java.io.PrintStream(java.io.OutputStream.nullOutputStream()));

        XMLCodec codec = new XMLCodec();

        // 1. Verifica carregamento da GLC (glc.jff)
        File glcFile = Path.of(args[0], "docs", "diagramas", "AV2", "glc.jff").toFile();
        Grammar cfg = (Grammar) codec.decode(glcFile, Collections.emptyMap());
        int prodCount = cfg.getProductions().length;
        report.println("GLC (glc.jff): carregada pelo JFLAP 7.1 com " + prodCount + " producoes");
        if (prodCount != 9) {
            System.err.println("GLC esperava 9 producoes, obtido: " + prodCount);
            System.exit(1);
        }

        int total = 0;
        int failures = 0;

        // 2. Valida ap.jff (PushdownAutomaton real + detector de determinismo do JFLAP)
        File apFile = Path.of(args[0], "docs", "diagramas", "AV2", "ap.jff").toFile();
        PushdownAutomaton pda = (PushdownAutomaton) codec.decode(apFile, Collections.emptyMap());
        State[] ndStates = new PDANondeterminismDetector().getNondeterministicStates(pda);
        int apCount = 0;
        int apErrors = 0;
        for (String line : Files.readAllLines(Path.of(args[1], "ap.tsv"), StandardCharsets.UTF_8)) {
            if (line.isEmpty()) continue;
            String[] fields = line.split("\t", -1);
            boolean expected = fields[0].equals("1");
            String input = new String(Base64.getDecoder().decode(fields[1]), StandardCharsets.UTF_8);
            boolean obtained = simulateJflapPdaByFinalState(pda, input);
            if (obtained != expected) {
                if (apErrors < 5) {
                    System.err.println("AP divergencia: entrada=" + input + " esperado=" + expected + " obtido=" + obtained);
                }
                apErrors++;
            }
            apCount++;
        }
        report.println(
            "AP (ap.jff): " + pda.getStates().length + " estados, "
            + ndStates.length + " estados nao-deterministicos, "
            + apCount + " casos, " + apErrors + " divergencias"
        );
        total += apCount;
        failures += apErrors;

        // 3. Valida all.jff diretamente com TMTransducer + TMSimulator oficiais do JFLAP 7.1
        File allFile = Path.of(args[0], "docs", "diagramas", "AV2", "all.jff").toFile();
        Document allDoc = DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(allFile);
        TuringMachine tm = (TuringMachine) new TMTransducer().fromDOM(allDoc);
        TMSimulator tmSim = new TMSimulator((Automaton) tm);
        int allCount = 0;
        int allErrors = 0;
        for (String line : Files.readAllLines(Path.of(args[1], "all.tsv"), StandardCharsets.UTF_8)) {
            if (line.isEmpty()) continue;
            String[] fields = line.split("\t", -1);
            boolean expected = fields[0].equals("1");
            String input = new String(Base64.getDecoder().decode(fields[1]), StandardCharsets.UTF_8);
            Configuration[] init = tmSim.getInitialConfigurations(input);
            TMConfiguration cur = (TMConfiguration) init[0];
            boolean obtained = false;
            int maxSteps = (input.length() + 2) * (input.length() + 2) + 20;
            for (int step = 0; step < maxSteps; step++) {
                if (cur.isAccept() && tm.isFinalState(cur.getCurrentState())) {
                    obtained = true;
                    break;
                }
                int headPos = cur.getTapes()[0].getTapeHead();
                if (headPos < 0 || headPos >= input.length()) {
                    throw new AssertionError("JFLAP ALL violou limites da fita em " + input + " (head=" + headPos + ")");
                }
                ArrayList next = tmSim.stepConfiguration(cur);
                if (next.isEmpty()) {
                    break;
                }
                cur = (TMConfiguration) next.get(0);
            }
            if (obtained != expected) {
                if (allErrors < 5) {
                    System.err.println("ALL divergencia: entrada=" + input + " esperado=" + expected + " obtido=" + obtained);
                }
                allErrors++;
            }
            allCount++;
        }
        report.println(
            "ALL (all.jff): " + tm.getStates().length + " estados, "
            + allCount + " casos, " + allErrors + " divergencias"
        );
        total += allCount;
        failures += allErrors;

        report.println("JFLAP AV2: " + total + " casos, " + failures + " divergencias");
        if (failures != 0 || ndStates.length != 0) {
            System.exit(1);
        }
    }
}
