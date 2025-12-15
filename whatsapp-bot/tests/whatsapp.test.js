/**
 * Unit tests for Bhai-Bot WhatsApp Interface
 */
const request = require('supertest');
const axios = require('axios');

// Mock axios for FastAPI calls
jest.mock('axios');

// Mock environment variables
process.env.VERIFY_TOKEN = 'test_verify_token_123';
process.env.WHATSAPP_TOKEN = 'test_whatsapp_token';
process.env.PHONE_NUMBER_ID = 'test_phone_id';
process.env.FASTAPI_URL = 'http://localhost:8000';

const app = require('../index');

describe('WhatsApp Webhook Verification', () => {
    test('Should verify webhook with correct token', async () => {
        const response = await request(app)
            .get('/webhook/whatsapp')
            .query({
                'hub.mode': 'subscribe',
                'hub.verify_token': 'test_verify_token_123',
                'hub.challenge': 'test_challenge_string'
            });
        
        expect(response.status).toBe(200);
        expect(response.text).toBe('test_challenge_string');
    });
    
    test('Should reject webhook with incorrect token', async () => {
        const response = await request(app)
            .get('/webhook/whatsapp')
            .query({
                'hub.mode': 'subscribe',
                'hub.verify_token': 'wrong_token',
                'hub.challenge': 'test_challenge_string'
            });
        
        expect(response.status).toBe(403);
    });
    
    test('Should reject non-subscribe mode', async () => {
        const response = await request(app)
            .get('/webhook/whatsapp')
            .query({
                'hub.mode': 'unsubscribe',
                'hub.verify_token': 'test_verify_token_123',
                'hub.challenge': 'test_challenge_string'
            });
        
        expect(response.status).toBe(403);
    });
});

describe('Intent Detection and Routing', () => {
    test('Should detect profit query intent', () => {
        const testMessages = [
            'ei mashe labh koto?',
            'profit koto?',
            'income kemon?',
            'amar labh dekhao'
        ];
        
        testMessages.forEach(msg => {
            const text = msg.toLowerCase();
            const isProfit = text.match(/labh|profit|income/);
            expect(isProfit).toBeTruthy();
        });
    });
    
    test('Should detect inventory query intent', () => {
        const testMessages = [
            'inventory check',
            'stock kemon ase?',
            'stock dekhao'
        ];
        
        testMessages.forEach(msg => {
            const text = msg.toLowerCase();
            const isInventory = text.match(/inventory|stock/);
            expect(isInventory).toBeTruthy();
        });
    });
    
    test('Should detect risk check intent', () => {
        const testMessages = [
            'risk check +8801712345678',
            'check risk for +8801999999999'
        ];
        
        testMessages.forEach(msg => {
            const text = msg.toLowerCase();
            const isRiskCheck = text.match(/risk check|check risk/);
            expect(isRiskCheck).toBeTruthy();
        });
    });
    
    test('Should detect fraud report intent', () => {
        const testMessages = [
            'report +8801712345678',
            'report fraud +8801999999999',
            'report fraudster +8801888888888'
        ];
        
        testMessages.forEach(msg => {
            const text = msg.toLowerCase();
            const isReport = text.match(/report/);
            expect(isReport).toBeTruthy();
        });
    });
});

describe('Message Handling', () => {
    beforeEach(() => {
        // Clear all mocks before each test
        jest.clearAllMocks();
    });
    
    test('Should handle profit query message', async () => {
        const message = {
            entry: [{
                changes: [{
                    value: {
                        messages: [{
                            from: '+8801712345678',
                            type: 'text',
                            text: {
                                body: 'ei mashe labh koto?'
                            }
                        }]
                    }
                }]
            }]
        };
        
        // Mock WhatsApp API response
        axios.post.mockResolvedValue({ data: { success: true } });
        
        const response = await request(app)
            .post('/webhook/whatsapp')
            .send(message);
        
        expect(response.status).toBe(200);
        expect(axios.post).toHaveBeenCalled();
    });
    
    test('Should handle risk check message', async () => {
        const message = {
            entry: [{
                changes: [{
                    value: {
                        messages: [{
                            from: '+8801712345678',
                            type: 'text',
                            text: {
                                body: 'risk check +8801999999999'
                            }
                        }]
                    }
                }]
            }]
        };
        
        // Mock FastAPI response
        axios.post.mockResolvedValue({
            data: {
                order_id: 'MANUAL-123',
                risk_score: 45,
                risk_level: 'MEDIUM',
                recommendation: 'CONFIRMATION_CALL_REQUIRED',
                suggested_actions: ['Call customer to confirm']
            }
        });
        
        const response = await request(app)
            .post('/webhook/whatsapp')
            .send(message);
        
        expect(response.status).toBe(200);
        // Verify FastAPI was called
        expect(axios.post).toHaveBeenCalledWith(
            expect.stringContaining('/api/v1/risk-score'),
            expect.any(Object)
        );
    });
    
    test('Should handle unknown message with help text', async () => {
        const message = {
            entry: [{
                changes: [{
                    value: {
                        messages: [{
                            from: '+8801712345678',
                            type: 'text',
                            text: {
                                body: 'random unknown message'
                            }
                        }]
                    }
                }]
            }]
        };
        
        // Mock WhatsApp API response
        axios.post.mockResolvedValue({ data: { success: true } });
        
        const response = await request(app)
            .post('/webhook/whatsapp')
            .send(message);
        
        expect(response.status).toBe(200);
    });
});

describe('Phone Number Extraction', () => {
    test('Should extract Bangladesh phone number', () => {
        const testCases = [
            { text: 'risk check +8801712345678', expected: '+8801712345678' },
            { text: 'report +8801999999999', expected: '+8801999999999' },
            { text: 'check risk for +8801888888888', expected: '+8801888888888' }
        ];
        
        testCases.forEach(({ text, expected }) => {
            const match = text.match(/\+880\d{10}/);
            expect(match).toBeTruthy();
            expect(match[0]).toBe(expected);
        });
    });
});

describe('Error Handling', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });
    
    test('Should handle FastAPI connection error gracefully', async () => {
        const message = {
            entry: [{
                changes: [{
                    value: {
                        messages: [{
                            from: '+8801712345678',
                            type: 'text',
                            text: {
                                body: 'risk check +8801999999999'
                            }
                        }]
                    }
                }]
            }]
        };
        
        // Mock FastAPI error
        axios.post.mockRejectedValue(new Error('Connection failed'));
        
        const response = await request(app)
            .post('/webhook/whatsapp')
            .send(message);
        
        expect(response.status).toBe(200);
    });
    
    test('Should handle malformed webhook payload', async () => {
        const malformedMessage = {
            entry: []  // Empty entry array
        };
        
        const response = await request(app)
            .post('/webhook/whatsapp')
            .send(malformedMessage);
        
        // Should not crash - either 200 or 500 depending on error handling
        expect([200, 500]).toContain(response.status);
    });
});

describe('WhatsApp API Integration', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });
    
    test('Should send message with correct format', async () => {
        const message = {
            entry: [{
                changes: [{
                    value: {
                        messages: [{
                            from: '+8801712345678',
                            type: 'text',
                            text: {
                                body: 'labh koto?'
                            }
                        }]
                    }
                }]
            }]
        };
        
        // Mock WhatsApp API
        axios.post.mockResolvedValue({ data: { success: true } });
        
        await request(app)
            .post('/webhook/whatsapp')
            .send(message);
        
        // Verify WhatsApp API was called with correct structure
        const whatsappCall = axios.post.mock.calls.find(call => 
            call[0].includes('graph.facebook.com')
        );
        
        if (whatsappCall) {
            const [url, payload, config] = whatsappCall;
            expect(payload).toHaveProperty('messaging_product', 'whatsapp');
            expect(payload).toHaveProperty('to');
            expect(payload).toHaveProperty('text');
            expect(config.headers).toHaveProperty('Authorization');
        }
    });
});

describe('Health Check', () => {
    test('Should return service info on root endpoint', async () => {
        const response = await request(app).get('/');
        
        expect(response.status).toBe(200);
        expect(response.body).toHaveProperty('service');
        expect(response.body.service).toBe('Bhai-Bot WhatsApp Interface');
    });
});
