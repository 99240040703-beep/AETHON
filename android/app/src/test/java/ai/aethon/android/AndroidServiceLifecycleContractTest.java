package ai.aethon.android;

import org.junit.Test;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

import static org.junit.Assert.assertTrue;

public final class AndroidServiceLifecycleContractTest {
    private static String read(String relative) throws Exception {
        Path path = Paths.get("src/main", relative);
        return Files.readString(path);
    }

    @Test
    public void manifestDeclaresNonExportedDataSyncService() throws Exception {
        String manifest = read("AndroidManifest.xml");
        assertTrue(manifest.contains("android:name=\".AndroidCommandService\""));
        assertTrue(manifest.contains("android:exported=\"false\""));
        assertTrue(manifest.contains("android:foregroundServiceType=\"dataSync\""));
    }

    @Test
    public void wakeServiceUsesEvolvePhraseAndRejectsLegacyPhrase() throws Exception {
        String wake = read("java/ai/aethon/android/WakeWordService.java");
        assertTrue(wake.contains("WAKE_PHRASE = "hey evolve""));
        assertTrue(wake.contains("String[] prefixes = {"));
        assertTrue(wake.contains("WAKE_PHRASE"));
        assertTrue(!wake.contains("hey assistant"));
    }

    @Test
    public void activityUsesEvolveWakePhrase() throws Exception {
        String activity = read("java/ai/aethon/android/MainActivity.java");
        assertTrue(activity.contains("Hey Evolve"));
    }

    @Test
    public void activityConnectsSpeechToEvolveVoiceApi() throws Exception {
        String activity = read("java/ai/aethon/android/MainActivity.java");
        assertTrue(activity.contains("EVOLVE_VOICE_SESSIONS"));
        assertTrue(activity.contains("evolveWakeAsync"));
        assertTrue(activity.contains("/wake"));
        assertTrue(activity.contains("/listen"));
        assertTrue(activity.contains("/transcript"));
        assertTrue(activity.contains("/sleep"));
    }

    @Test
    public void evolveSessionUsesHeyEvolveWakePhrase() throws Exception {
        String activity = read("java/ai/aethon/android/MainActivity.java");
        assertTrue(activity.contains("wake.put(\"phrase\",\"Hey Evolve\")"));
    }

    @Test
    public void wakeListenerRoutesThroughEvolveLifecycle() throws Exception {
        String activity = read("java/ai/aethon/android/MainActivity.java");
        assertTrue(activity.contains("Hey Evolve"));
        assertTrue(activity.contains("evolveRequestAsyncListen"));
        assertTrue(activity.contains("evolveRequestAsyncTranscript"));
        assertTrue(activity.contains("MainActivity.this::sendAssistant"));
        assertTrue(activity.contains("String[] wakes={\"hey evolve\",\"ok evolve\",\"okay evolve\"}"));
    }

    @Test
    public void activityStartsAndStopsService() throws Exception {
        String activity = read("java/ai/aethon/android/MainActivity.java");
        assertTrue(activity.contains("AndroidCommandService.start(this,base,id,token)"));
        assertTrue(activity.contains("AndroidCommandService.stop(this)"));
    }
}
