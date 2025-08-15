const functions = require('firebase-functions');

// Example HTTP function for /api/health
exports.api = functions.https.onRequest((req, res) => {
  if (req.path === '/health') {
    res.json({ status: "ok", timestamp: Date.now() });
  } else if (req.path === '/status') {
    res.json({ status: "running" });
  } else {
    res.status(404).send("Not found");
  }
});