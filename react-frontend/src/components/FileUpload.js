import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useDropzone } from 'react-dropzone';

const FileUpload = () => {
  const [files, setFiles] = useState([]);
  const [reportSource, setReportSource] = useState('web');

  useEffect(() => {
    if (reportSource === 'local') {
      axios.get('/files').then(response => {
        setFiles(response.data);
      });
    }
  }, [reportSource]);

  const onDrop = (acceptedFiles) => {
    const formData = new FormData();
    formData.append('file', acceptedFiles[0]);

    axios.post('/upload', formData).then(response => {
      setFiles([...files, response.data]);
    });
  };

  const handleDelete = (hash) => {
    axios.delete(`/delete/${hash}`).then(() => {
      setFiles(files.filter(file => !file.startsWith(hash)));
    });
  };

  const { getRootProps, getInputProps } = useDropzone({ onDrop });

  return (
    <div>
      <select onChange={(e) => setReportSource(e.target.value)} value={reportSource}>
        <option value="web">The Web</option>
        <option value="local">My Documents</option>
      </select>

      {reportSource === 'local' && (
        <div>
          {files.length === 0 ? (
            <div {...getRootProps()} className="dropzone">
              <input {...getInputProps()} />
              <p>Drag 'n' drop some files here, or click to select files</p>
            </div>
          ) : (
            <ul>
              {files.map(file => (
                <li key={file}>
                  {file}
                  <button onClick={() => handleDelete(file.split('-')[0])}>Delete</button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};

export default FileUpload;