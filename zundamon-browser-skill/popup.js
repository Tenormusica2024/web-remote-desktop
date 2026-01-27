/**
 * Zundamon Voice for Claude - Popup Script
 */

const statusDiv = document.getElementById('status');
const enableToggle = document.getElementById('enableToggle');
const vtsToggle = document.getElementById('vtsToggle');
const vrmToggle = document.getElementById('vrmToggle');
const testButton = document.getElementById('testButton');

// 初期化
async function init() {
  // 設定読み込み
  const settings = await chrome.storage.sync.get(['enabled', 'vtsEnabled', 'vrmEnabled']);
  enableToggle.checked = settings.enabled !== false;
  vtsToggle.checked = settings.vtsEnabled === true;
  vrmToggle.checked = settings.vrmEnabled === true;
  
  // VOICEVOX接続確認
  checkVoicevoxConnection();
}

// VOICEVOX接続確認
async function checkVoicevoxConnection() {
  try {
    const response = await fetch('http://localhost:50021/version');
    if (response.ok) {
      const version = await response.text();
      showStatus('success', `✅ VOICEVOX接続成功 (${version})`);
    } else {
      showStatus('error', '❌ VOICEVOX接続失敗');
    }
  } catch (error) {
    showStatus('error', '❌ VOICEVOX未起動 - VOICEVOX Engineを起動してください');
  }
}

// ステータス表示
function showStatus(type, message) {
  statusDiv.className = `status ${type}`;
  statusDiv.textContent = message;
}

// トグルスイッチ変更
enableToggle.addEventListener('change', async () => {
  const enabled = enableToggle.checked;
  await chrome.storage.sync.set({ enabled });
  
  // 全タブのcontent scriptに通知
  const tabs = await chrome.tabs.query({ url: 'https://claude.ai/*' });
  tabs.forEach(tab => {
    chrome.tabs.sendMessage(tab.id, { action: 'toggle', enabled });
  });
  
  showStatus('info', enabled ? '🔊 音声通知: 有効' : '🔇 音声通知: 無効');
});

// VTubeStudioトグル変更
vtsToggle.addEventListener('change', async () => {
  const vtsEnabled = vtsToggle.checked;
  await chrome.storage.sync.set({ vtsEnabled });
  
  // VRM連携と排他制御
  if (vtsEnabled && vrmToggle.checked) {
    vrmToggle.checked = false;
    await chrome.storage.sync.set({ vrmEnabled: false });
  }
  
  showStatus('info', vtsEnabled ? '🎭 VTubeStudio連携: 有効（ページ再読み込み必要）' : '🎭 VTubeStudio連携: 無効');
});

// VRMトグル変更
vrmToggle.addEventListener('change', async () => {
  const vrmEnabled = vrmToggle.checked;
  await chrome.storage.sync.set({ vrmEnabled });
  
  // VTubeStudio連携と排他制御
  if (vrmEnabled && vtsToggle.checked) {
    vtsToggle.checked = false;
    await chrome.storage.sync.set({ vtsEnabled: false });
  }
  
  showStatus('info', vrmEnabled ? '🎨 VRM連携: 有効（ページ再読み込み＋Bridge Server起動必要）' : '🎨 VRM連携: 無効');
});

// テストボタン
testButton.addEventListener('click', async () => {
  testButton.disabled = true;
  testButton.textContent = '再生中...';
  
  try {
    // VOICEVOX API直接呼び出し
    const text = 'テストメッセージです。音声通知が正常に動作しています。';
    
    // 音声クエリ生成
    const queryResponse = await fetch(
      `http://localhost:50021/audio_query?text=${encodeURIComponent(text)}&speaker=3`,
      { method: 'POST' }
    );
    
    if (!queryResponse.ok) {
      throw new Error('音声クエリ生成失敗');
    }
    
    const audioQuery = await queryResponse.json();
    
    // 音声合成
    const synthesisResponse = await fetch(
      'http://localhost:50021/synthesis?speaker=3',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(audioQuery)
      }
    );
    
    if (!synthesisResponse.ok) {
      throw new Error('音声合成失敗');
    }
    
    const audioData = await synthesisResponse.arrayBuffer();
    
    // Web Audio APIで再生
    const audioContext = new AudioContext();
    const audioBuffer = await audioContext.decodeAudioData(audioData);
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);
    
    source.onended = () => {
      showStatus('success', '✅ テスト再生完了');
      testButton.disabled = false;
      testButton.textContent = '🎤 テスト再生';
    };
    
    source.start(0);
    showStatus('info', '🔊 再生中...');
    
  } catch (error) {
    showStatus('error', `❌ テスト失敗: ${error.message}`);
    testButton.disabled = false;
    testButton.textContent = '🎤 テスト再生';
  }
});

// 初期化実行
init();
