const Log = require('../models/log');
const Report = require('../models/report');
const slugify = require('slugify');

exports.saveLog = ({rabbitMessage}) => {

    let newLog = new Log();
   
    Object.assign(newLog, rabbitMessage);
        
    newLog.save((err, result) => {
        if (err) {
            console.log('this is the error from the newLog.save call:', err);
        } else {
            console.log('saved log successfully')
        }
    })
}

exports.saveReport = ({rabbitMessage}) => {

    Report.exists({task_id: rabbitMessage.task_id}).then(async result => {
        console.log('result of search for report: ',result)
        if(result==false){
            let newReport = new Report();
            Object.assign(newReport, rabbitMessage);
            newReport.body = [{"type": "paragraph", "content": rabbitMessage.paragraph}]
            newReport.slug = rabbitMessage.question ? slugify(rabbitMessage.question, {lower: true, strict: true}) : rabbitMessage.task_id;
            newReport.title = rabbitMessage.question;

            newReport.save((err, result) => {
                if (err) {
                    console.log('this is the error from the newReport.save call:', err);
                } else {
                    console.log('saved report successfully')
                }
            })
        } else {
            const filter = { task_id: rabbitMessage.task_id };
            const update = {$push: {'body': 
                {"type": "paragraph","content": rabbitMessage.paragraph}}}

            await Report.findOneAndUpdate(filter, update);
        }
    })
}