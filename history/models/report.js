const mongoose = require('mongoose');
const { ObjectId } = mongoose.Schema;

const reportSchema = new mongoose.Schema(
    {   
        task_id: {
            type: String,
            trim: true,
            max: 160
        },
        question: {
            type: String,
            trim: true,
            max: 500
        },
        agent: {
            type: String,
            trim: true,
            max: 500
        },
        agent_role_prompt: {
            type: String,
            trim: true,
            max: 500
        },
        title: {
            type: String,
            trim: true,
            min: 3,
            max: 160
            // required: true
        },
        slug: {
            type: String,
            index: true
        },
        body: { 
            type : Array , 
            "default" : []
        }
    },
    { timestamps: true }
);

module.exports = mongoose.model('Report', reportSchema);
