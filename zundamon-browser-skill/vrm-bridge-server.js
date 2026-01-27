/**
 * VRM WebSocket Bridge Server
 * ブラウザ(WebSocket) ⇔ VSeeFace/3tene(OSC over UDP)
 *
 * 必要なパッケージ:
 * npm install ws osc
 */

const WebSocket = require('ws');
const osc = require('osc');
const dgram = require('dgram'); // Node.js組み込みUDPモジュール

// 設定
const WEBSOCKET_PORT = 8765;
const OSC_TARGET_HOST = '127.0.0.1';
const OSC_TARGET_PORT = 39540; // VMC Protocol default port

// dgram UDP Socketの作成（oscライブラリの代替）
const udpSocket = dgram.createSocket('udp4');
let oscPortReady = false;
let oscPortHealthy = false;

udpSocket.on('error', (err) => {
  console.error('❌ UDP Socketエラー:', err);
  oscPortHealthy = false;
});

udpSocket.on('listening', () => {
  const address = udpSocket.address();
  console.log(`✅ UDP Socket準備完了: ${address.address}:${address.port}`);
  oscPortReady = true;
  oscPortHealthy = true;
  
  // 初期化処理を開始
  setTimeout(() => {
    setArmPose(true);
    console.log('🎯 初期化完了: 腕を下げた状態に設定');
    
    // ランダム表情変化を開始
    startRandomEmotionChange();
  }, 500);
});

// UDP Socketをバインド（任意のポートで受信待機）
udpSocket.bind(); // ポート指定なし = OSが自動割り当て

// WebSocketサーバーの作成
const wss = new WebSocket.Server({ port: WEBSOCKET_PORT });

console.log(`🚀 VRM WebSocket Bridge Server起動 (WebSocket: ${WEBSOCKET_PORT}, OSC: ${OSC_TARGET_PORT})`);

// 現在の感情状態（口パクと統合するため）
let currentEmotion = {
  emotion: 'neutral',
  intensity: 0,
  blendShapes: {}
};

// リセットタイマー（新しい感情が来たらキャンセルするため）
let emotionResetTimer = null;
let gestureResetTimer = null;

// ランダム表情変化タイマー
let randomEmotionTimer = null;
let isRandomEmotionActive = false;

// UDP Socket健全性チェック（5秒ごと）
setInterval(() => {
  console.log(`🏥 UDP Socketヘルスチェック: ready=${oscPortReady}, healthy=${oscPortHealthy}`);
}, 5000);

// WebSocket接続ハンドリング
wss.on('connection', (ws) => {
  console.log('✅ WebSocketクライアント接続');

  ws.on('message', (data) => {
    try {
      const message = JSON.parse(data);

      // 口パクメッセージのログは抑制（高頻度のため）
      if (message.type !== 'blend' ||
          (message.shapes && (message.shapes.A !== 0 || message.shapes.I !== 0 || message.shapes.U !== 0 || message.shapes.E !== 0 || message.shapes.O !== 0))) {
        console.log('📨 受信メッセージ:', message);
      }

      if (message.type === 'blend') {
        // BlendShape値をOSCメッセージに変換
        sendBlendShapesToOSC(message.shapes);
      } else if (message.type === 'bone') {
        // ボーン位置・回転をOSCメッセージに変換
        sendBonePoseToOSC(message.boneName, message.position, message.rotation);
      } else if (message.type === 'setArmPose') {
        // 腕のポーズ設定（音声再生時の制御）
        console.log('🎯 setArmPose呼び出し: isPlaying =', message.isPlaying);
        setArmPose(message.isPlaying);
      } else if (message.type === 'setEmotion') {
        // 感情表現設定（BlendShape制御）
        console.log('🎭 setEmotion呼び出し: emotion =', message.emotion, 'intensity =', message.intensity);
        setEmotion(message.emotion, message.intensity);
      } else if (message.type === 'setGesture') {
        // ジェスチャー設定（ボーン制御）
        console.log('👋 setGesture呼び出し: emotion =', message.emotion, 'intensity =', message.intensity);
        setGesture(message.emotion, message.intensity);
      }

    } catch (error) {
      console.error('❌ メッセージ解析エラー:', error);
    }
  });

  ws.on('close', () => {
    console.log('❌ WebSocketクライアント切断');
  });

  ws.on('error', (error) => {
    console.error('❌ WebSocketエラー:', error);
  });

  // 接続成功を通知
  ws.send(JSON.stringify({
    type: 'connected',
    message: 'VRM Bridge Server ready'
  }));
});

/**
 * BlendShape値をVMC Protocol OSCメッセージとして送信
 * 感情BlendShapeと口パクBlendShapeを統合して送信
 */
function sendBlendShapesToOSC(shapes) {
  try {
    // UDP Socket健全性を確認
    if (!oscPortHealthy) {
      console.error('❌ UDP Socketが不健全な状態です - 送信をスキップ');
      console.log(`🔍 現在の状態: ready=${oscPortReady}, healthy=${oscPortHealthy}`);
      return;
    }
    
    // 現在の感情BlendShapeと統合
    const isEmotionOnly = Object.keys(shapes).some(key => ['Joy', 'Sorrow', 'Angry', 'Surprised', 'Fun'].includes(key));
    if (isEmotionOnly) {
      console.log(`🔍 sendBlendShapesToOSC呼び出し: shapes =`, JSON.stringify(shapes));
      console.log(`🔍 currentEmotion.blendShapes =`, JSON.stringify(currentEmotion.blendShapes));
    }
    const mergedShapes = { ...currentEmotion.blendShapes, ...shapes };

    // 各BlendShapeに対してOSCメッセージ送信
    for (const [name, value] of Object.entries(mergedShapes)) {
      const oscMessage = {
        address: '/VMC/Ext/Blend/Val',
        args: [
          { type: 's', value: name },    // BlendShape名
          { type: 'f', value: value }    // 値（0-1）
        ]
      };
      
      // oscライブラリでエンコードしてdgramで送信
      const oscPacket = osc.writePacket(oscMessage);
      udpSocket.send(oscPacket, OSC_TARGET_PORT, OSC_TARGET_HOST);
    }

    // 適用コマンド送信
    const applyMessage = {
      address: '/VMC/Ext/Blend/Apply',
      args: []
    };
    const applyPacket = osc.writePacket(applyMessage);
    udpSocket.send(applyPacket, OSC_TARGET_PORT, OSC_TARGET_HOST);

    // 送信ログは完全に抑制（感情表現のログは別の場所で出力）

  } catch (error) {
    console.error('❌ OSC送信エラー:', error);
  }
}

/**
 * ボーン位置・回転をVMC Protocol OSCメッセージとして送信
 * @param {string} boneName - ボーン名（例: "LeftUpperArm", "RightUpperArm"）
 * @param {Object} position - 位置 {x, y, z}
 * @param {Object} rotation - 回転（Quaternion）{x, y, z, w}
 */
function sendBonePoseToOSC(boneName, position, rotation) {
  try {
    const oscMessage = {
      address: '/VMC/Ext/Bone/Pos',
      args: [
        { type: 's', value: boneName },
        { type: 'f', value: position.x },
        { type: 'f', value: position.y },
        { type: 'f', value: position.z },
        { type: 'f', value: rotation.x },
        { type: 'f', value: rotation.y },
        { type: 'f', value: rotation.z },
        { type: 'f', value: rotation.w }
      ]
    };
    
    const oscPacket = osc.writePacket(oscMessage);
    udpSocket.send(oscPacket, OSC_TARGET_PORT, OSC_TARGET_HOST);
    console.log(`📤 ボーンOSC送信: ${boneName}`);

  } catch (error) {
    console.error('❌ ボーンOSC送信エラー:', error);
  }
}

/**
 * ルート位置を送信（VMC Protocolの必須要件）
 */
function sendRootTransform() {
  try {
    const oscMessage = {
      address: '/VMC/Ext/Root/Pos',
      args: [
        { type: 's', value: 'root' },
        { type: 'f', value: 0.0 },  // position x
        { type: 'f', value: 0.0 },  // position y
        { type: 'f', value: 0.0 },  // position z
        { type: 'f', value: 0.0 },  // rotation x
        { type: 'f', value: 0.0 },  // rotation y
        { type: 'f', value: 0.0 },  // rotation z
        { type: 'f', value: 1.0 }   // rotation w
      ]
    };
    
    const oscPacket = osc.writePacket(oscMessage);
    udpSocket.send(oscPacket, OSC_TARGET_PORT, OSC_TARGET_HOST);
    console.log('📤 ルートTransform送信');
  } catch (error) {
    console.error('❌ ルートTransform送信エラー:', error);
  }
}

/**
 * 腕のポーズを設定（音声再生時の制御）
 * @param {boolean} isPlaying - true: 腕を下げる, false: T-Poseに戻す
 */
function setArmPose(isPlaying) {
  try {
    // VMC Protocol要件: ボーン送信前にルート位置を送信
    sendRootTransform();

    // 常に腕を70度下げた状態に設定（ランダム表情変化時も維持）
    const armQuaternion = eulerToQuaternion(0, 0, 70);  // Z軸70度回転
    
    // LeftUpperArm（左上腕）
    sendBonePoseToOSC('LeftUpperArm',
      { x: 0.0, y: 0.0, z: 0.0 },
      armQuaternion
    );

    // RightUpperArm（右上腕）
    const armQuaternionR = eulerToQuaternion(0, 0, -70);  // Z軸-70度回転
    sendBonePoseToOSC('RightUpperArm',
      { x: 0.0, y: 0.0, z: 0.0 },
      armQuaternionR
    );

    console.log('🎵 腕を70度下げた状態に設定');
  } catch (error) {
    console.error('❌ 腕ポーズ設定エラー:', error);
  }
}

/**
 * 感情表現を設定（BlendShape制御）
 * @param {string} emotion - 感情名（joy, sad, angry, surprised, 等）
 * @param {number} intensity - 強度 (0.0-1.0)
 */
function setEmotion(emotion, intensity) {
  try {
    // 感情ごとのBlendShapeマッピング
    const emotionBlendShapes = {
      'joy': {           // 喜び
        Joy: intensity * 1.5,
        Fun: intensity * 1.3
      },
      'sad': {           // 悲しみ
        Sorrow: intensity * 2.2,  // 悲しみの強度を2.2倍に増加（0.2増加）
        Joy: 0.0
      },
      'surprised': {     // 驚き
        Surprised: intensity * 1.5,
        Joy: intensity * 0.8
      },
      'angry': {         // 怒り
        Angry: intensity * 2.0,  // 怒りの強度を2.0倍に増加
        //Sorrow: intensity * 1.3
      },
      'confused': {      // 困惑
        Surprised: intensity * 0.9,
        Sorrow: intensity * 1.0  // 困惑時の悲しみ強度を0.8→1.0に増加（+0.2）
      },
      'worried': {       // 心配
        Sorrow: intensity * 1.4,  // 心配の強度を増加
        Surprised: intensity * 0.7
      },
      'excited': {       // 興奮
        Joy: intensity * 1.5,
        Fun: intensity * 1.5,
        Surprised: intensity * 0.8
      },
      'apologetic': {    // 謝罪
        Sorrow: intensity * 1.5  // 謝罪の強度を増加
      },
      'grateful': {      // 感謝
        Joy: intensity * 1.4,
        Fun: intensity * 1.0
      },
      'encouraging': {   // 励まし
        Joy: intensity * 1.2,
        Fun: intensity * 1.1
      },
      'explaining': {    // 説明
        // ニュートラルに近い落ち着いた表情
        Joy: intensity * 0.7
      },
      'questioning': {   // 質問
        Surprised: intensity * 0.9,
        Joy: intensity * 0.7
      },
      'celebrating': {   // 祝福
        Joy: intensity * 1.5,
        Fun: intensity * 1.5,
        Surprised: intensity * 1.0
      },
      'disappointed': {  // 失望
        Sorrow: intensity * 1.8  // 失望の強度を増加
      },
      'impressed': {     // 感心
        Surprised: intensity * 1.1,
        Joy: intensity * 1.2
      },
      'playful': {       // ふざけ
        Fun: intensity * 1.5,
        Joy: intensity * 1.3
      },
      'serious': {       // 真剣
        // ニュートラル
        Joy: 0.0,
        Sorrow: intensity * 0.7
      },
      'neutral': {       // 中立
        Joy: 0.0,
        Sorrow: 0.0,
        Angry: 0.0,
        Surprised: 0.0,
        Fun: 0.0
      }
    };

    // 指定された感情のBlendShapeを取得
    const blendShapes = emotionBlendShapes[emotion] || emotionBlendShapes['neutral'];

    // ランダム表情変化を一時停止（音声再生中の感情表現を優先）
    // 音声再生中は一時停止するが、再生終了後も自動で再開しない
    const wasRandomActive = isRandomEmotionActive;
    if (isRandomEmotionActive && emotion !== 'neutral') {
      stopRandomEmotionChange();
    }
    
    // 注意: この関数は音声再生中の感情表現用
    // ランダム表情変化にはsetEmotionWithoutReset()を使用すること

    // 既存のリセットタイマーをキャンセル
    if (emotionResetTimer) {
      clearTimeout(emotionResetTimer);
      emotionResetTimer = null;
    }

    // 現在の感情状態を保存（口パクと統合するため）
    currentEmotion = {
      emotion: emotion,
      intensity: intensity,
      blendShapes: blendShapes
    };

    // BlendShapeを送信
    sendBlendShapesToOSC(blendShapes);

    console.log(`🎭 感情表現送信: ${emotion} (強度: ${intensity}) BlendShapes: ${JSON.stringify(blendShapes)}`);

    // 感情表示後、5秒後にニュートラルに戻す（neutralの場合は戻さない）
    if (emotion !== 'neutral') {
      emotionResetTimer = setTimeout(() => {
        const neutralBlendShapes = emotionBlendShapes['neutral'];
        currentEmotion = {
          emotion: 'neutral',
          intensity: 0.0,
          blendShapes: neutralBlendShapes
        };
        sendBlendShapesToOSC(neutralBlendShapes);
        console.log(`🎭 ニュートラルに戻しました`);
        emotionResetTimer = null;
        
        // ランダム表情変化は自動再開しない（手動で再開が必要）
        // 音声再生が終わったからといってランダム表情を勝手に再開すると、
        // ユーザーが音声再生を停止した意図を無視してしまう
      }, 5000);  // 5秒後にニュートラルに戻す
    }

  } catch (error) {
    console.error('❌ 感情表現設定エラー:', error);
  }
}

/**
 * 感情表現を設定（自動リセットなし - ランダム表情用）
 * @param {string} emotion - 感情名（joy, sad, angry, surprised, 等）
 * @param {number} intensity - 強度 (0.0-1.0)
 */
function setEmotionWithoutReset(emotion, intensity) {
  const callTime = Date.now();
  console.log(`🟢 setEmotionWithoutReset実行開始: ${emotion} (強度: ${intensity}) - 時刻: ${callTime}`);
  
  try {
    // 感情ごとのBlendShapeマッピング
    const emotionBlendShapes = {
      'joy': {           // 喜び
        Joy: intensity * 1.5,
        Fun: intensity * 1.3
      },
      'sad': {           // 悲しみ
        Sorrow: intensity * 2.2,  // 悲しみの強度を2.2倍に増加（0.2増加）
        Joy: 0.0
      },
      'surprised': {     // 驚き
        Surprised: intensity * 1.5,
        Joy: intensity * 0.8
      },
      'angry': {         // 怒り
        Angry: intensity * 2.0,  // 怒りの強度を2.0倍に増加
        //Sorrow: intensity * 1.3
      },
      'confused': {      // 困惑
        Surprised: intensity * 0.9,
        Sorrow: intensity * 1.0  // 困惑時の悲しみ強度を0.8→1.0に増加（+0.2）
      },
      'worried': {       // 心配
        Sorrow: intensity * 1.4,  // 心配の強度を増加
        Surprised: intensity * 0.7
      },
      'excited': {       // 興奮
        Joy: intensity * 1.5,
        Fun: intensity * 1.5,
        Surprised: intensity * 0.8
      },
      'apologetic': {    // 謝罪
        Sorrow: intensity * 1.5  // 謝罪の強度を増加
      },
      'grateful': {      // 感謝
        Joy: intensity * 1.4,
        Fun: intensity * 1.0
      },
      'encouraging': {   // 励まし
        Joy: intensity * 1.2,
        Fun: intensity * 1.1
      },
      'explaining': {    // 説明
        // ニュートラルに近い落ち着いた表情
        Joy: intensity * 0.7
      },
      'questioning': {   // 質問
        Surprised: intensity * 0.9,
        Joy: intensity * 0.7
      },
      'celebrating': {   // 祝福
        Joy: intensity * 1.5,
        Fun: intensity * 1.5,
        Surprised: intensity * 1.0
      },
      'disappointed': {  // 失望
        Sorrow: intensity * 1.8  // 失望の強度を増加
      },
      'impressed': {     // 感心
        Surprised: intensity * 1.1,
        Joy: intensity * 1.2
      },
      'playful': {       // ふざけ
        Fun: intensity * 1.5,
        Joy: intensity * 1.3
      },
      'serious': {       // 真剣
        // ニュートラル
        Joy: 0.0,
        Sorrow: intensity * 0.7
      },
      'neutral': {       // 中立
        Joy: 0.0,
        Sorrow: 0.0,
        Angry: 0.0,
        Surprised: 0.0,
        Fun: 0.0
      }
    };

    // 指定された感情のBlendShapeを取得
    const blendShapes = emotionBlendShapes[emotion] || emotionBlendShapes['neutral'];

    // 既存のリセットタイマーをキャンセル（ランダム表情用）
    if (emotionResetTimer) {
      clearTimeout(emotionResetTimer);
      emotionResetTimer = null;
    }

    // 現在の感情状態を保存（口パクと統合するため）
    currentEmotion = {
      emotion: emotion,
      intensity: intensity,
      blendShapes: blendShapes
    };

    // BlendShapeを送信
    console.log(`📤 OSC送信前: currentEmotion =`, JSON.stringify(currentEmotion));
    sendBlendShapesToOSC(blendShapes);
    console.log(`✅ OSC送信完了`);

    console.log(`🎭 感情表現送信（自動リセットなし）: ${emotion} (強度: ${intensity})`);
    console.log(`🟢 setEmotionWithoutReset完了 - 次の呼び出しまでこの表情を維持`);

    // 自動リセットなし - 次のランダム表情まで継続

  } catch (error) {
    console.error('❌ 感情表現設定エラー:', error);
  }
}

/**
 * ジェスチャーを設定（ボーン制御）
 * @param {string} emotion - 感情名（ジェスチャーマッピング用）
 * @param {number} intensity - 強度 (0.0-1.0)
 */
function setGesture(emotion, intensity) {
  try {
    // ルートTransform送信（VMC Protocol必須）
    sendRootTransform();

    // 感情ごとのジェスチャーマッピング
    const gesturePatterns = {
      'joy': () => {
        if (intensity >= 0.8) {
          // 喜び（強度0.8以上）: 両手で万歳（Z軸60度 + Handボーンで手のひらを前に）
          const quaternionL = eulerToQuaternion(0, 0, -60);  // 左腕: Z軸のみで上げる
          sendBonePoseToOSC('LeftUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionL);
          const quaternionR = eulerToQuaternion(0, 0, 60);   // 右腕: Z軸のみで上げる
          sendBonePoseToOSC('RightUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionR);

          // Handボーンで手のひらを前に向ける（Y軸回転）
          const handL = eulerToQuaternion(0, -45, 0);  // 左手: Y軸-45度で手のひらを前に
          sendBonePoseToOSC('LeftHand', { x: 0.0, y: 0.0, z: 0.0 }, handL);
          const handR = eulerToQuaternion(0, 45, 0);   // 右手: Y軸+45度で手のひらを前に
          sendBonePoseToOSC('RightHand', { x: 0.0, y: 0.0, z: 0.0 }, handR);
        } else {
          // 喜び（通常）: 両腕を少し上げる（Z軸で軽く開く）
          const angleL = -45 * intensity;  // 0-(-45)度
          const quaternionL = eulerToQuaternion(0, 0, angleL);
          sendBonePoseToOSC('LeftUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionL);
          const angleR = 45 * intensity;   // 0-45度
          const quaternionR = eulerToQuaternion(0, 0, angleR);
          sendBonePoseToOSC('RightUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionR);
        }
      },
      'sad': () => {
        // 悲しみ: ジェスチャーなし（腕を下げた状態を維持）
        const quaternionL = eulerToQuaternion(0, 0, 75);   // 左腕を下げる
        sendBonePoseToOSC('LeftUpperArm', { x: 0.0, y: 0.0, z: 90.0 }, quaternionL);
        const quaternionR = eulerToQuaternion(0, 0, -75);  // 右腕を下げる
        sendBonePoseToOSC('RightUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionR);
      },
      'surprised': () => {
        // 驚き: 両手を上げて手のひらをこちらに向ける（±70度）
        const quaternionL = eulerToQuaternion(0, -45, -70);  // 左腕: Y軸-45度で手のひらを前に + Z軸-70度で上げる
        sendBonePoseToOSC('LeftUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionL);
        const quaternionR = eulerToQuaternion(0, 45, 70);    // 右腕: Y軸+45度で手のひらを前に + Z軸+70度で上げる
        sendBonePoseToOSC('RightUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionR);
      },

      'angry': () => {
        // 怒り: 両腕を上げて肘を曲げ、拳を握る

        // 上腕: 腕を高く上げる
        const quaternionL = eulerToQuaternion(0, 0, 70);
        sendBonePoseToOSC('LeftUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionL);
        const quaternionR = eulerToQuaternion(0, 0, -70);
        sendBonePoseToOSC('RightUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionR);

        // 前腕: 肘を90度曲げる
        const elbowL = eulerToQuaternion(0, 90, 70);
        sendBonePoseToOSC('LeftLowerArm', { x: 0.0, y: 0.0, z: 0.0 }, elbowL);
        const elbowR = eulerToQuaternion(0, -90, -70);
        sendBonePoseToOSC('RightLowerArm', { x: 0.0, y: 0.0, z: 0.0 }, elbowR);

        // 手: 拳を握る風（手のひらを内側に）
        const handL = eulerToQuaternion(0, 90, -70);
        sendBonePoseToOSC('LeftHand', { x: 0.0, y: 0.0, z: 0.0 }, handL);
        const handR = eulerToQuaternion(0, -90, 70);
        sendBonePoseToOSC('RightHand', { x: 0.0, y: 0.0, z: 0.0 }, handR);
      },
      'confused': () => {
        // 上腕: 腕を下げる
        const quaternionL = eulerToQuaternion(0, 0, 70);
        sendBonePoseToOSC('LeftUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionL);
        const quaternionR = eulerToQuaternion(0, 0, -70);
        sendBonePoseToOSC('RightUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionR);

        // 前腕: 肘を90度曲げる
        const elbowL = eulerToQuaternion(0, 90, 70);
        sendBonePoseToOSC('LeftLowerArm', { x: 0.0, y: 0.0, z: 0.0 }, elbowL);
        const elbowR = eulerToQuaternion(0, -90, -70);
        sendBonePoseToOSC('RightLowerArm', { x: 0.0, y: 0.0, z: 0.0 }, elbowR);

        // 手: 手を開いて拒否のポーズ
        const handL = eulerToQuaternion(0, 90, -70);
        sendBonePoseToOSC('LeftHand', { x: 0.0, y: 0.0, z: 0.0 }, handL);
        const handR = eulerToQuaternion(0, -90, 70);
        sendBonePoseToOSC('RightHand', { x: 0.0, y: 0.0, z: 0.0 }, handR);
      },
      'worried': () => {
        // 心配: 両手を合わせる風
        const angle = 40 * intensity;
        const quaternionL = eulerToQuaternion(angle, 0, 20);
        sendBonePoseToOSC('LeftUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionL);
        const quaternionR = eulerToQuaternion(angle, 0, -20);
        sendBonePoseToOSC('RightUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionR);
      },
      'excited': () => {
        // 興奮: 両腕を上げてガッツポーズ（Z軸60度 + Y軸で手のひらを前に）
        const quaternionL = eulerToQuaternion(0, -45, -60);  // 左腕: Y軸-45度で手のひらを前に
        sendBonePoseToOSC('LeftUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionL);
        const quaternionR = eulerToQuaternion(0, 45, 60);    // 右腕: Y軸+45度で手のひらを前に
        sendBonePoseToOSC('RightUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionR);
      },
      'apologetic': () => {
        // 謝罪: 両腕を前で下げてお詫びのポーズ
        const quaternionL = eulerToQuaternion(0, 45, 60);  // 左腕: Y軸-45度で手のひらを前に
					　// （前後）（上下）
        sendBonePoseToOSC('LeftUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionL);
        const quaternionR = eulerToQuaternion(0, -45, -60);    // 右腕: Y軸+45度で手のひらを前に
        sendBonePoseToOSC('RightUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionR);
      },
      'grateful': () => {
        // 感謝: 片手を上げてお礼のポーズ
        const angle = -30 * intensity;
        const quaternionL = eulerToQuaternion(angle, 0, -40);
        sendBonePoseToOSC('LeftUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionL);
        sendBonePoseToOSC('RightUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, { x: 0.383, y: 0.0, z: 0.0, w: 0.924 });
      },
      'encouraging': () => {
        // 励まし: 片手を上げてファイトポーズ
        const angle = -15 * intensity;
	const quaternionL = eulerToQuaternion(angle, 0, -75, -75);
        const quaternionR = eulerToQuaternion(angle, -90, 30, -70);
        sendBonePoseToOSC('RightUpperArm', { x: 0.0, y: 0.0, z: 90.0 }, quaternionR);
        sendBonePoseToOSC('LeftUpperArm', { x: 0.0, y: -90.0, z: 0.0 }, { x: 0.383, y: 0.0, z: 0.0, w: 0.924 });
      },
      'explaining': () => {
        // 説明: 片手を前に出して説明するポーズ
        const angle = 35 * intensity;
        const quaternionL = eulerToQuaternion(angle, 0, -15);
        sendBonePoseToOSC('LeftUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionL);
        sendBonePoseToOSC('RightUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, { x: 0.383, y: 0.0, z: 0.0, w: 0.924 });
      },
      'questioning': () => {
        // 質問: 片手を上げて疑問のポーズ
        const angle = -25 * intensity;
        const quaternionR = eulerToQuaternion(angle, 0, 25);
        sendBonePoseToOSC('RightUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionR);
        sendBonePoseToOSC('LeftUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, { x: 0.383, y: 0.0, z: 0.0, w: 0.924 });
      },
      'celebrating': () => {
        // 祝福: 両腕を高く上げて祝福（Z軸60度 + Y軸で手のひらを前に）
        const quaternionL = eulerToQuaternion(0, 45, -60);  // 左腕: Y軸-45度で手のひらを前に
        sendBonePoseToOSC('LeftUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionL);
        const quaternionR = eulerToQuaternion(0, -45, 60);    // 右腕: Y軸+45度で手のひらを前に
        sendBonePoseToOSC('RightUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionR);
      },
      'disappointed': () => {
        // 失望: 腕を下げてがっかり
        const angle = -80 * intensity;
        const quaternion = eulerToQuaternion(angle, 0, 0);
        sendBonePoseToOSC('LeftUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternion);
        sendBonePoseToOSC('RightUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternion);
      },
      'impressed': () => {
        // 感心: 両手を合わせて感心のポーズ
        const angle = 50 * intensity;
        const quaternionL = eulerToQuaternion(angle, 0, 25);
        sendBonePoseToOSC('LeftUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionL);
        const quaternionR = eulerToQuaternion(angle, 0, -25);
        sendBonePoseToOSC('RightUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionR);
      },
      'playful': () => {
        // ふざけ: 片手を上げてピース
        const angle = -20 * intensity;
        const quaternionL = eulerToQuaternion(angle, 0, -35);
        sendBonePoseToOSC('LeftUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionL);
        sendBonePoseToOSC('RightUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, { x: 0.383, y: 0.0, z: 0.0, w: 0.924 });
      },
      'serious': () => {
        // 真剣: 両腕を下げて真剣な姿勢
        const quaternion = { x: 0.383, y: 0.0, z: 0.0, w: 0.924 };
        sendBonePoseToOSC('LeftUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternion);
        sendBonePoseToOSC('RightUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternion);
      },
      'neutral': () => {
        // 中立: 腕を完全に下げた状態（デフォルト位置）
        const quaternionL = eulerToQuaternion(0, 0, 75);   // 左腕を下げる（Z軸+75度）
        sendBonePoseToOSC('LeftUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionL);
        const quaternionR = eulerToQuaternion(0, 0, -75);  // 右腕を下げる（Z軸-75度）
        sendBonePoseToOSC('RightUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionR);
      },
      'exasperated': () => {
        // 呆れた: 肩をすくめるジェスチャー（軽く腕を上げる）
        const quaternionL = eulerToQuaternion(0, 0, -30);  // 左腕を軽く上げる
        sendBonePoseToOSC('LeftUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionL);
        const quaternionR = eulerToQuaternion(0, 0, 30);   // 右腕を軽く上げる
        sendBonePoseToOSC('RightUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionR);
      }
    };

    // 既存のリセットタイマーをキャンセル
    if (gestureResetTimer) {
      clearTimeout(gestureResetTimer);
      gestureResetTimer = null;
    }

    // 指定された感情のジェスチャーを実行
    const gestureFunc = gesturePatterns[emotion] || gesturePatterns['neutral'];
    gestureFunc();

    // ジェスチャーを5秒後に自動でリセット（デフォルト位置 = 腕を完全に下げる）
    gestureResetTimer = setTimeout(() => {
      // 上腕をリセット
      const quaternionL = eulerToQuaternion(0, 0, 75);   // 左腕を完全に下げる
      sendBonePoseToOSC('LeftUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionL);
      const quaternionR = eulerToQuaternion(0, 0, -75);  // 右腕を完全に下げる
      sendBonePoseToOSC('RightUpperArm', { x: 0.0, y: 0.0, z: 0.0 }, quaternionR);

      // 前腕（肘）をリセット
      const elbowReset = eulerToQuaternion(0, 0, 0);
      sendBonePoseToOSC('LeftLowerArm', { x: 0.0, y: 0.0, z: 0.0 }, elbowReset);
      sendBonePoseToOSC('RightLowerArm', { x: 0.0, y: 0.0, z: 0.0 }, elbowReset);

      // 手首をリセット
      const handReset = eulerToQuaternion(0, 0, 0);
      sendBonePoseToOSC('LeftHand', { x: 0.0, y: 0.0, z: 0.0 }, handReset);
      sendBonePoseToOSC('RightHand', { x: 0.0, y: 0.0, z: 0.0 }, handReset);

      console.log('👋 ジェスチャーリセット（腕・肘・手首）');
      gestureResetTimer = null;
    }, 5000);  // 5秒後にリセット

    console.log(`👋 ジェスチャー送信: ${emotion} (強度: ${intensity})`);

  } catch (error) {
    console.error('❌ ジェスチャー設定エラー:', error);
  }
}

/**
 * Euler角をQuaternionに変換
 * @param {number} x - X軸回転（度）
 * @param {number} y - Y軸回転（度）
 * @param {number} z - Z軸回転（度）
 * @return {Object} Quaternion {x, y, z, w}
 */
function eulerToQuaternion(x, y, z) {
  const degToRad = Math.PI / 180;
  const xRad = x * degToRad / 2;
  const yRad = y * degToRad / 2;
  const zRad = z * degToRad / 2;

  const cx = Math.cos(xRad);
  const sx = Math.sin(xRad);
  const cy = Math.cos(yRad);
  const sy = Math.sin(yRad);
  const cz = Math.cos(zRad);
  const sz = Math.sin(zRad);

  return {
    x: sx * cy * cz - cx * sy * sz,
    y: cx * sy * cz + sx * cy * sz,
    z: cx * cy * sz - sx * sy * cz,
    w: cx * cy * cz + sx * sy * sz
  };
}

/**
 * ランダム表情変化を開始
 * デフォルト50% + 各種感情をランダムに表示
 */
function startRandomEmotionChange() {
  if (isRandomEmotionActive) {
    console.log('⚠️ ランダム表情変化は既にアクティブです');
    return;
  }
  
  // 既存のタイマーを完全にクリア
  if (randomEmotionTimer) {
    clearTimeout(randomEmotionTimer);
    randomEmotionTimer = null;
  }
  
  isRandomEmotionActive = true;
  console.log('🎲 ランダム表情変化を開始します（10秒後に最初の変化）');
  
  // 使用する感情リスト（neutral以外）
  const emotions = [
    'joy', 'sad', 'surprised', 'confused', 'worried',
    'excited', 'grateful', 'playful', 'questioning'
  ];
  
  function scheduleNextEmotion() {
    console.log('🔄 scheduleNextEmotion実行開始');
    
    if (!isRandomEmotionActive) {
      console.log('⚠️ ランダム表情変化が非アクティブ - スキップ');
      return;
    }
    
    const currentTime = Date.now();
    console.log(`⏰ 現在時刻: ${currentTime}`);
    
    // 50%の確率でneutral、50%の確率でランダム感情
    const useNeutral = Math.random() < 0.5;
    
    if (useNeutral) {
      console.log('🎲 neutral選択 - setEmotionWithoutReset呼び出し');
      setEmotionWithoutReset('neutral', 0);
      console.log('✅ setEmotionWithoutReset(neutral)完了');
    } else {
      // ランダムな感情を選択
      const randomEmotion = emotions[Math.floor(Math.random() * emotions.length)];
      const randomIntensity = 0.3 + Math.random() * 0.4; // 0.3-0.7の範囲
      
      console.log(`🎲 ${randomEmotion}選択 - setEmotionWithoutReset呼び出し (強度: ${randomIntensity.toFixed(2)})`);
      setEmotionWithoutReset(randomEmotion, randomIntensity);
      console.log(`✅ setEmotionWithoutReset(${randomEmotion})完了`);
    }
    
    // 10秒後に次の表情変化をスケジュール
    randomEmotionTimer = setTimeout(scheduleNextEmotion, 10000);
    console.log(`⏱️ 次の表情変化を10秒後（${currentTime + 10000}）にスケジュールしました`);
  }
  
  // 最初の表情変化を10秒後にスケジュール
  randomEmotionTimer = setTimeout(scheduleNextEmotion, 10000);
}

/**
 * ランダム表情変化を停止
 */
function stopRandomEmotionChange() {
  if (!isRandomEmotionActive) {
    console.log('⚠️ ランダム表情変化は既に停止しています');
    return;
  }
  
  isRandomEmotionActive = false;
  
  if (randomEmotionTimer) {
    clearTimeout(randomEmotionTimer);
    randomEmotionTimer = null;
    console.log('🛑 ランダム表情変化を停止しました（タイマークリア）');
  } else {
    console.log('🛑 ランダム表情変化を停止しました（タイマーなし）');
  }
}

// エラーハンドリング
process.on('uncaughtException', (error) => {
  console.error('❌ 予期しないエラー:', error);
});

process.on('SIGINT', () => {
  console.log('\n🛑 サーバー停止中...');

  oscPort.close();
  wss.close(() => {
    console.log('✅ サーバー停止完了');
    process.exit(0);
  });
});
