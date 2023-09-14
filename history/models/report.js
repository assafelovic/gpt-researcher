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
        },
        excerpt: {
            type: String,
            max: 1000
        },
        mtitle: {
            type: String
        },
        mdesc: {
            type: String
        },
        hidden: { 
            type: Boolean, 
            default: false 
        },
        page_link: {
            type: String
        },
        
        categories: [{ 
            type: ObjectId, 
            ref: 'Category'
        }],
        tags: [{ 
            type: ObjectId, 
            ref: 'Tag'
        }],
        postedBy: {
            type: ObjectId,
            ref: 'User'
        }
    },
    { timestamps: true }
);

module.exports = mongoose.model('Report', reportSchema);
