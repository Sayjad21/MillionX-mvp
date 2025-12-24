const express = require("express");
const axios = require("axios");
require("dotenv").config();

const app = express();
app.use(express.json());

// Configuration
const FASTAPI_URL = process.env.FASTAPI_URL || "http://localhost:8000";
const WHATSAPP_TOKEN = process.env.WHATSAPP_TOKEN;
const PHONE_NUMBER_ID = process.env.PHONE_NUMBER_ID;
const VERIFY_TOKEN = process.env.VERIFY_TOKEN || "millionx_verify_token_123";
const PORT = process.env.PORT || 3000;

// ============= WEBHOOK VERIFICATION =============
app.get("/webhook/whatsapp", (req, res) => {
  const mode = req.query["hub.mode"];
  const token = req.query["hub.verify_token"];
  const challenge = req.query["hub.challenge"];

  console.log("📞 Webhook verification attempt:", { mode, token });

  if (mode === "subscribe" && token === VERIFY_TOKEN) {
    console.log("✅ Webhook verified successfully!");
    res.status(200).send(challenge);
  } else {
    console.log("❌ Webhook verification failed");
    res.sendStatus(403);
  }
});

// ============= WEBHOOK MESSAGE HANDLER =============
app.post("/webhook/whatsapp", async (req, res) => {
  console.log("📨 Incoming webhook:", JSON.stringify(req.body, null, 2));

  try {
    // Extract message from webhook payload
    const entry = req.body.entry?.[0];
    const changes = entry?.changes?.[0];
    const value = changes?.value;
    const messages = value?.messages;

    if (!messages || messages.length === 0) {
      console.log("⚠️ No messages in webhook payload");
      return res.sendStatus(200);
    }

    const message = messages[0];
    const from = message.from;
    const messageType = message.type;

    console.log(`📱 Message from ${from}, type: ${messageType}`);

    let response = "";

    // Handle text messages
    if (messageType === "text") {
      const text = message.text.body.toLowerCase();
      response = await routeTextMessage(text, from);
    }
    // Handle image uploads
    else if (messageType === "image") {
      response = await handleImageUpload(message);
    }
    // Other message types
    else {
      response =
        "🤖 Sorry, I can only handle text messages and images for now.";
    }

    // Send response back to user
    await sendWhatsAppMessage(from, response);

    res.sendStatus(200);
  } catch (error) {
    console.error("❌ Error processing message:", error);
    // Return 200 to prevent WhatsApp from retrying (graceful degradation)
    res.sendStatus(200);
  }
});

// ============= MESSAGE ROUTING =============
async function routeTextMessage(text, from) {
  console.log(`🔍 Routing message: "${text}" from ${from}`);

  // Intent: Profit/Revenue Query
  if (text.match(/labh|profit|income|revenue|earning/)) {
    return await handleProfitQuery(from);
  }

  // Intent: Inventory Check
  if (text.match(/inventory|stock|product/)) {
    return await handleInventoryQuery(from);
  }

  // Intent: Risk Check
  if (text.match(/risk check/)) {
    const phone = extractPhoneNumber(text);
    if (phone) {
      return await handleRiskCheck(phone);
    } else {
      return '❌ Please provide phone number.\nExample: "risk check +8801712345678"';
    }
  }

  // Intent: Inventory Forecast (NEW AI FEATURE!)
  if (text.match(/forecast|predict|demand|restock|copilot/)) {
    return await handleForecastQuery(text);
  }

  // Intent: Report Fraudster (NETWORK EFFECT!)
  if (text.match(/report/)) {
    const phone = extractPhoneNumber(text);
    if (phone) {
      return await handleReportFraudster(phone, from);
    } else {
      return '❌ Please provide phone number to report.\nExample: "report +8801712345678"';
    }
  }

  // Default: Help message
  return getHelpMessage();
}

// ============= INTENT HANDLERS =============
async function handleProfitQuery(merchantPhone) {
  console.log(`💰 Handling profit query for ${merchantPhone}`);

  try {
    // Call FastAPI for real profit data
    const response = await axios.get(
      `${FASTAPI_URL}/api/v1/merchant/profit?merchant_id=${merchantPhone}`
    );
    const data = response.data;

    return (
      `📊 *${data.period} Profit Summary*\n\n` +
      `💰 Revenue: Tk ${data.revenue.toLocaleString()}\n` +
      `💸 Costs: Tk ${data.estimated_costs.toLocaleString()}\n` +
      `✅ *Net Profit: Tk ${data.net_profit.toLocaleString()}* (${data.trend_vs_previous} vs prev)\n\n` +
      `🔥 Top seller: ${data.top_seller.product} (${data.top_seller.units_sold} units)\n` +
      `📦 Total orders: ${data.total_orders}\n` +
      `📈 Margin: ${data.profit_margin_pct}%`
    );
  } catch (error) {
    console.error("❌ Profit query failed:", error.message);
    return "❌ Could not fetch profit data. Please try again later.";
  }
}

async function handleInventoryQuery(merchantPhone) {
  console.log(`📦 Handling inventory query for ${merchantPhone}`);

  try {
    // Call FastAPI for real inventory data
    const response = await axios.get(
      `${FASTAPI_URL}/api/v1/merchant/inventory?merchant_id=${merchantPhone}&threshold=10`
    );
    const data = response.data;

    let reply = `📦 *Inventory Status*\n\n`;

    if (data.low_stock_count > 0) {
      reply += `⚠️ *${data.low_stock_count} Low Stock Items:*\n`;
      data.low_stock_alerts.forEach((alert, i) => {
        reply += `• ${alert.product_name} - ${alert.estimated_stock} left\n`;
      });
    } else {
      reply += `✅ All stock levels healthy!\n`;
    }

    reply += `\n💡 Tip: ${data.tip}`;
    
    if (data.trending_products && data.trending_products.length > 0) {
      reply += `\n\n🔥 Trending: ${data.trending_products.join(", ")}`;
    }

    return reply;
  } catch (error) {
    console.error("❌ Inventory query failed:", error.message);
    return "❌ Could not fetch inventory data. Please try again later.";
  }
}

async function handleForecastQuery(text) {
  console.log(`🤖 Handling forecast query: ${text}`);

  try {
    // Check if user wants specific product
    const productMatch = text.match(/PROD-\d+/);
    const url = productMatch
      ? `${FASTAPI_URL}/api/v1/inventory/forecast?product_id=${productMatch[0]}`
      : `${FASTAPI_URL}/api/v1/inventory/forecast?limit=3`;

    console.log(`🔗 Calling AI: ${url}`);
    const response = await axios.get(url);
    const data = response.data;

    let reply = "🤖 *Inventory Copilot AI* 🤖\n\n";

    if (productMatch) {
      // Single product response
      reply += `📦 *${data.product_name || productMatch[0]}*\n`;
      reply += `${
        data.recommendation || data.message || "Forecast complete"
      }\n\n`;
      reply += `🕒 ${new Date().toLocaleTimeString("en-BD")}`;
    } else {
      // Batch forecast response
      const products = data.products || [];
      products.forEach((p, i) => {
        reply += `${i + 1}. *${p.product_name || p.product_id}*\n`;
        reply += `   ${p.recommendation}\n\n`;
      });
      reply += `✅ Analyzed ${products.length} products\n`;
      reply += `🕒 ${new Date().toLocaleTimeString("en-BD")}`;
    }

    return reply;
  } catch (error) {
    console.error("❌ Forecast query failed:", error.message);
    return '❌ AI forecast temporarily unavailable. Try:\n• "forecast" for top products\n• "forecast PROD-130" for specific item';
  }
}

async function handleRiskCheck(phone) {
  console.log(`🛡️ Checking risk for ${phone}`);

  try {
    const response = await axios.post(`${FASTAPI_URL}/api/v1/risk-score`, {
      order_id: `MANUAL-${Date.now()}`,
      merchant_id: "DEMO-MERCHANT",
      customer_phone: phone,
      delivery_address: {
        area: "Unknown",
        city: "Dhaka",
        postal_code: "",
      },
      order_details: {
        total_amount: 500,
        currency: "BDT",
        items_count: 1,
        is_first_order: false,
      },
      timestamp: new Date().toISOString(),
    });

    const data = response.data;

    return (
      `🛡️ *COD Shield Risk Check*\n\n` +
      `📞 Phone: ${phone}\n` +
      `📊 Risk Score: *${data.risk_score}/100*\n` +
      `⚠️ Risk Level: *${data.risk_level}*\n\n` +
      `💡 *Recommendation:*\n${data.recommendation.replace(/_/g, " ")}\n\n` +
      `✅ *Suggested Actions:*\n${data.suggested_actions
        .map((a, i) => `${i + 1}. ${a}`)
        .join("\n")}`
    );
  } catch (error) {
    console.error("❌ Risk check failed:", error.message);
    return "❌ Risk check failed. Please try again or contact support.";
  }
}

async function handleReportFraudster(phone, reporterPhone) {
  console.log(`🚨 Reporting fraudster ${phone} by ${reporterPhone}`);

  try {
    const response = await axios.post(
      `${FASTAPI_URL}/api/v1/blacklist/add`,
      null,
      {
        params: {
          phone: phone,
          reason: `Reported by merchant ${reporterPhone}`,
        },
      }
    );

    const data = response.data;

    return (
      `🚨 *Fraudster Reported!*\n\n` +
      `📞 Phone: ${phone}\n` +
      `✅ Added to network blacklist\n` +
      `📊 Total reports: ${data.total_hits}\n\n` +
      `💪 Thanks for protecting the community!`
    );
  } catch (error) {
    console.error("❌ Report failed:", error.message);
    return "❌ Failed to report. Please try again.";
  }
}

async function handleImageUpload(message) {
  console.log("📷 Image upload received");

  // TODO: Phase 2 - Download and process image for product cataloging
  return (
    `📷 *Image Received!*\n\n` +
    `✅ Image saved for processing\n` +
    `🚧 Auto-cataloging coming in Phase 2!\n\n` +
    `For now, please add product details manually.`
  );
}

// ============= HELPER FUNCTIONS =============
function extractPhoneNumber(text) {
  // Extract phone number from text (Bangladesh format)
  const phoneRegex = /\+?880\d{10}|\+?\d{11,15}/;
  const match = text.match(phoneRegex);
  return match ? match[0] : null;
}

function getHelpMessage() {
  return (
    `🤖 *Bhai-Bot here!*\n\n` +
    `I can help you with:\n\n` +
    `💰 *"labh koto?"* - Check your profit\n` +
    `📦 *"inventory check"* - View stock status\n` +
    `🤖 *"forecast"* - AI demand prediction\n` +
    `🤖 *"forecast PROD-130"* - Specific product\n` +
    `🛡️ *"risk check +880..."* - Check customer risk\n` +
    `🚨 *"report +880..."* - Report a fraudster\n` +
    `📷 *Send image* - Add product (coming soon!)\n\n` +
    `Just type your question naturally!`
  );
}

async function sendWhatsAppMessage(to, text) {
  try {
    console.log(`📤 Sending message to ${to}`);

    const response = await axios.post(
      `https://graph.facebook.com/v18.0/${PHONE_NUMBER_ID}/messages`,
      {
        messaging_product: "whatsapp",
        to: to,
        text: { body: text },
      },
      {
        headers: {
          Authorization: `Bearer ${WHATSAPP_TOKEN}`,
          "Content-Type": "application/json",
        },
      }
    );

    console.log("✅ Message sent successfully");
    return response.data;
  } catch (error) {
    console.error(
      "❌ Failed to send message:",
      error.response?.data || error.message
    );
    throw error;
  }
}

// ============= HEALTH CHECK =============
app.get("/health", (req, res) => {
  res.json({
    status: "healthy",
    service: "Bhai-Bot WhatsApp Interface",
    fastapi_url: FASTAPI_URL,
    timestamp: new Date().toISOString(),
  });
});

// ============= ROOT ENDPOINT =============
app.get("/", (req, res) => {
  res.json({
    service: "Bhai-Bot WhatsApp Interface",
    version: "1.0.0",
    endpoints: {
      webhook: "/webhook/whatsapp",
      health: "/health",
    },
  });
});

// ============= START SERVER =============
// Only start server if not being required as a module (for tests)
if (require.main === module) {
  app.listen(PORT, () => {
    console.log("🚀 Bhai-Bot WhatsApp server started!");
    console.log(`📡 Listening on port ${PORT}`);
    console.log(`🔗 FastAPI URL: ${FASTAPI_URL}`);
    console.log(
      `📞 Phone Number ID: ${PHONE_NUMBER_ID ? "✅ Configured" : "❌ Missing"}`
    );
    console.log(
      `🔑 WhatsApp Token: ${WHATSAPP_TOKEN ? "✅ Configured" : "❌ Missing"}`
    );
    console.log("\n💡 Configure webhook URL in Meta Dashboard:");
    console.log(`   https://your-domain.com/webhook/whatsapp`);
    console.log(`   Verify Token: ${VERIFY_TOKEN}\n`);
  });
}

module.exports = app;
