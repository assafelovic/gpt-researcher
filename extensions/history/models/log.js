const mongoose = require('mongoose');
const { ObjectId } = mongoose.Schema;

const logSchema = new mongoose.Schema(
    {
        task_id: {
            type: String,
            trim: true,
            min: 3,
            max: 160
        },
        question: {
            type: String,
            trim: true,
            min: 3,
            max: 500
        },
        agent: {
            type: String,
            trim: true,
            min: 3,
            max: 500
        },
        agent_role_prompt: {
            type: String,
            trim: true,
            min: 3,
            max: 500
        },
        type: {
            type: String,
            trim: true,
            min: 3,
            max: 160,
            // required: true
        },
        output: {
            type: {},
            // required: true,
            max: 2000000
        }
    },
    { timestamps: true }
);

module.exports = mongoose.model('Log', logSchema);