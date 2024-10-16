import React, { useCallback, useEffect, useState } from "react";
import axios from 'axios';
import { useDropzone } from 'react-dropzone';
import {getHost} from "@/helpers/getHost"

const FileUpload = () => {
  const [files, setFiles] = useState([]);
  const host = getHost();

  const fetchFiles = useCallback(async () => {
    try {
      const response = await axios.get(`${host}/files/`);
      setFiles(response.data.files);
    } catch (error) {
      console.error('Error fetching files:', error);
    }
  }, [host]);

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

  const onDrop = async (acceptedFiles: any[]) => {
    const formData = new FormData();
    acceptedFiles.forEach(file => {
      formData.append('file', file);
    });
    
    try {
      await axios.post(`${host}/upload/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      fetchFiles();
    } catch (error) {
      console.error('Error uploading files:', error);
    }
  };

  const deleteFile = async (filename: never) => {
    try {
      await axios.delete(`${host}/files/${filename}`);
      fetchFiles();
    } catch (error) {
      console.error('Error deleting file:', error);
    }
  };

  const { getRootProps, getInputProps } = useDropzone({ onDrop });

  return (
    <div className={"mb-4 w-full"}>
      <div {...getRootProps()} style={{ border: '2px dashed #cccccc', padding: '20px', textAlign: 'center' }}>
        <input {...getInputProps()} />
        <p>Drag &apos;n&apos; drop some files here, or click to select files</p>
      </div>
      {files.length > 0 && (
          <>
            <h2 className={"text-gray-900 mt-2 text-xl"}>Uploaded Files</h2>
            <ul role={"list"} className={"my-2 divide-y divide-gray-100"}>
              {files.map(file => (
                <li key={file} className={"flex justify-between gap-x-6 py-1"}>
                  <span className={"flex-1"}>{file}</span>
                  <button onClick={(e) => { e.preventDefault(); deleteFile(file) }}>
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5"
                        stroke="currentColor" className="size-6">
                      <path strokeLinecap="round" strokeLinejoin="round"
                            d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"/>
                    </svg>
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}
    </div>
  );
};

export default FileUpload;