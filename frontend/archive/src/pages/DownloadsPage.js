import React, { useState, useEffect } from 'react';
import { projectService } from '../services/api';

/**
 * Downloads page for accessing transcripts and audio files
 */
const DownloadsPage = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedProject, setSelectedProject] = useState(null);
  const [transcript, setTranscript] = useState('');
  const [showTranscript, setShowTranscript] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState(null);
  
  /**
   * Helper function to parse various date formats
   * @param {string} dateString - The date string to parse
   * @returns {Date|null} - A valid Date object or null if parsing fails
   */
  const parseDate = (dateString) => {
    if (!dateString || dateString === 'Unknown') return null;
    
    console.log(`Parsing date string: "${dateString}"`);
    
    // Try to parse as ISO date first
    let date = new Date(dateString);
    
    // Check if parsing was successful
    if (!isNaN(date.getTime())) {
      console.log(`Successfully parsed as standard date: ${date}`);
      return date;
    }
    
    // Try to parse date with 24-hour format from metadata: "April 7, 2025 20:44"
    let match = dateString.match(/(\w+)\s+(\d+),?\s+(\d+)\s+(\d{1,2}):(\d{2})(?:\s*(AM|PM))?/i);
    if (match) {
      console.log(`Matched 24-hour format: ${JSON.stringify(match)}`);
      const [_, month, day, year, hour, minute, ampm] = match;
      const months = {
        'January': 0, 'February': 1, 'March': 2, 'April': 3, 'May': 4, 'June': 5,
        'July': 6, 'August': 7, 'September': 8, 'October': 9, 'November': 10, 'December': 11
      };
      
      // Check if month is valid
      if (months[month] !== undefined) {
        let hours = parseInt(hour);
        
        // If AM/PM is specified, adjust hours accordingly
        if (ampm) {
          if (ampm.toUpperCase() === 'PM' && hours < 12) hours += 12;
          if (ampm.toUpperCase() === 'AM' && hours === 12) hours = 0;
        }
        
        date = new Date(
          parseInt(year),
          months[month],
          parseInt(day),
          hours,
          parseInt(minute)
        );
        
        if (!isNaN(date.getTime())) {
          console.log(`Successfully parsed with 24-hour format: ${date}`);
          return date;
        }
      }
    }
    
    // Try to parse date with full month name: "April 7, 2025 at 08:25 PM"
    match = dateString.match(/(\w+)\s+(\d+),?\s+(\d+)\s+at\s+(\d+):(\d+)\s+(\w+)/i);
    if (match) {
      console.log(`Matched full month pattern: ${JSON.stringify(match)}`);
      const [_, month, day, year, hour, minute, ampm] = match;
      const months = {
        'January': 0, 'February': 1, 'March': 2, 'April': 3, 'May': 4, 'June': 5,
        'July': 6, 'August': 7, 'September': 8, 'October': 9, 'November': 10, 'December': 11
      };
      
      // Check if month is valid
      if (months[month] !== undefined) {
        let hours = parseInt(hour);
        if (ampm.toUpperCase() === 'PM' && hours < 12) hours += 12;
        if (ampm.toUpperCase() === 'AM' && hours === 12) hours = 0;
        
        date = new Date(
          parseInt(year),
          months[month],
          parseInt(day),
          hours,
          parseInt(minute)
        );
        
        if (!isNaN(date.getTime())) {
          console.log(`Successfully parsed with full month: ${date}`);
          return date;
        }
      }
    }
    
    // Try to parse a timestamp from the project ID (e.g., "egDIqKLt2L4_20250407_204454")
    match = dateString.match(/(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/);
    if (!match && dateString.includes('_')) {
      // Try to extract timestamp from project ID instead
      const projectId = dateString.split('_')[1]; // Get the timestamp part
      if (projectId) {
        match = projectId.match(/(\d{4})(\d{2})(\d{2})_?(\d{2})?(\d{2})?(\d{2})?/);
      }
    }
    
    if (match) {
      console.log(`Matched timestamp format: ${JSON.stringify(match)}`);
      const [_, year, month, day, hour, minute, second] = match;
      
      date = new Date(
        parseInt(year),
        parseInt(month) - 1, // Months are 0-indexed in JS Date
        parseInt(day),
        parseInt(hour || '0'),
        parseInt(minute || '0'),
        parseInt(second || '0')
      );
      
      if (!isNaN(date.getTime())) {
        console.log(`Successfully parsed from timestamp: ${date}`);
        return date;
      }
    }
    
    console.warn(`Failed to parse date string: "${dateString}"`);
    return null;
  };
  
  // Load all projects when component mounts
  useEffect(() => {
    fetchProjects();
  }, []);
  
  /**
   * Fetches all projects and sorts them by date (newest first)
   */
  const fetchProjects = async () => {
    try {
      setLoading(true);
      const data = await projectService.getAllProjects();
      
      // Log the raw data to see what we're working with
      console.log('Raw project data:', data);
      
      // Enhance each project with a sortDate for consistent sorting
      const enhancedData = data.map(project => {
        // First try using the project's date field
        let sortDate = null;
        
        // Try to get a date from the timestamp field if present
        if (project.timestamp) {
          try {
            const timestampDate = new Date(project.timestamp);
            if (!isNaN(timestampDate.getTime())) {
              sortDate = timestampDate;
              console.log(`Project ${project.id} using timestamp field: ${sortDate}`);
            }
          } catch (e) {
            console.warn(`Failed to parse timestamp for ${project.id}: ${e.message}`);
          }
        }
        
        // If no valid timestamp, try parsing the date field
        if (!sortDate && project.date) {
          const parsedDate = parseDate(project.date);
          if (parsedDate) {
            sortDate = parsedDate;
            console.log(`Project ${project.id} using parsed date: ${sortDate}`);
          }
        }
        
        // If still no date, try extracting from project ID
        if (!sortDate && project.id && project.id.includes('_')) {
          const timestampPart = project.id.split('_')[1];
          if (timestampPart && timestampPart.length >= 8) {
            // Format like "20250407" (YYYYMMDD)
            try {
              const year = timestampPart.substring(0, 4);
              const month = timestampPart.substring(4, 6);
              const day = timestampPart.substring(6, 8);
              
              let hour = '00', minute = '00';
              if (timestampPart.length >= 12) {
                hour = timestampPart.substring(8, 10);
                minute = timestampPart.substring(10, 12);
              }
              
              const dateFromId = new Date(
                parseInt(year),
                parseInt(month) - 1, // Months are 0-indexed
                parseInt(day),
                parseInt(hour),
                parseInt(minute)
              );
              
              if (!isNaN(dateFromId.getTime())) {
                sortDate = dateFromId;
                console.log(`Project ${project.id} using date from ID: ${sortDate}`);
              }
            } catch (e) {
              console.warn(`Failed to extract date from ID ${project.id}: ${e.message}`);
            }
          }
        }
        
        // Return enhanced project with sort date
        return {
          ...project,
          sortDate
        };
      });
      
      // Sort the enhanced projects
      const sortedProjects = enhancedData.sort((a, b) => {
        // If both have sort dates, compare them
        if (a.sortDate && b.sortDate) {
          return b.sortDate - a.sortDate; // Newest first
        }
        
        // If only one has a sort date, prioritize it
        if (a.sortDate) return -1;
        if (b.sortDate) return 1;
        
        // Otherwise, fall back to ID comparison
        return b.id.localeCompare(a.id); // Descending order for IDs
      });
      
      // Explicitly log each project's sort date for verification
      sortedProjects.forEach((project, index) => {
        console.log(`Sorted[${index}]: "${project.id}" - SortDate: ${project.sortDate || 'None'} - OriginalDate: "${project.date}"`);
      });
      
      setProjects(sortedProjects);
      setError('');
    } catch (err) {
      console.error('Error fetching projects:', err);
      setError('Failed to load projects. Please try again later.');
    } finally {
      setLoading(false);
    }
  };
  
  // Load transcript when a project is selected
  const handleViewTranscript = async (project) => {
    try {
      setSelectedProject(project);
      setLoading(true);
      
      const result = await projectService.getTranscript(project.id);
      setTranscript(result.text);
      setShowTranscript(true);
      setError('');
    } catch (err) {
      console.error(`Error fetching transcript for project ${project.id}:`, err);
      setError('Failed to load transcript. Please try again later.');
      setShowTranscript(false);
    } finally {
      setLoading(false);
    }
  };
  
  // Format date for display
  const formatDate = (dateString) => {
    try {
      // If it's already a formatted date string, return it
      if (!dateString || dateString === 'Unknown') return 'Unknown';
      
      // Use our parseDate helper function to get a valid date object
      const date = parseDate(dateString);
      
      if (date && !isNaN(date.getTime())) {
        // Format in a standard way
        return date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        });
      }
      
      // If parsing failed, just return the original string
      return dateString;
    } catch (e) {
      console.error('Error formatting date:', e);
      return dateString || 'Unknown';
    }
  };
  
  // Format YouTube URL for display
  const formatYoutubeUrl = (url) => {
    if (!url) return '';
    
    // If URL is very long, truncate it for display
    if (url.length > 50) {
      return url.substring(0, 47) + '...';
    }
    return url;
  };
  
  // Download transcript as a text file
  const downloadTranscript = (projectId) => {
    projectService.downloadTranscript(projectId);
  };
  
  // Download audio file
  const downloadAudio = (projectId, filename) => {
    projectService.downloadAudio(projectId, filename);
  };
  
  // Copy transcript to clipboard
  const copyTranscript = () => {
    if (!transcript) return;
    
    navigator.clipboard.writeText(transcript)
      .then(() => {
        alert('Transcript copied to clipboard!');
      })
      .catch(err => {
        console.error('Could not copy text: ', err);
        alert('Failed to copy transcript. Please try manually selecting and copying the text.');
      });
  };
  
  // Show delete confirmation dialog
  const confirmDelete = (project) => {
    setProjectToDelete(project);
    setShowDeleteConfirm(true);
  };
  
  // Delete project
  const handleDeleteProject = async () => {
    if (!projectToDelete) return;
    
    try {
      setLoading(true);
      await projectService.deleteProject(projectToDelete.id);
      
      // If the deleted project is currently shown in transcript view, go back to list
      if (selectedProject && selectedProject.id === projectToDelete.id) {
        setShowTranscript(false);
      }
      
      // Refresh the project list
      fetchProjects();
      
      setShowDeleteConfirm(false);
      setProjectToDelete(null);
    } catch (err) {
      console.error(`Error deleting project ${projectToDelete.id}:`, err);
      setError('Failed to delete project. Please try again later.');
      setShowDeleteConfirm(false);
    }
  };
  
  // Get display name for the project
  const getProjectDisplayName = (project) => {
    // If project has a title, use it; otherwise use the ID
    return project.name || project.id.split('_')[0];
  };
  
  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '20px' }}>
      <h1>Downloads</h1>
      
      {loading && !showTranscript && (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          Loading...
        </div>
      )}
      
      {error && (
        <div style={{ 
          padding: '10px',
          backgroundColor: '#ffcccc',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          {error}
        </div>
      )}
      
      {!loading && projects.length === 0 && (
        <div style={{ 
          padding: '20px', 
          textAlign: 'center',
          backgroundColor: '#f9f9f9',
          borderRadius: '4px'
        }}>
          <p>No projects found. Start by processing a YouTube video on the Process Video page.</p>
        </div>
      )}
      
      {showTranscript && selectedProject ? (
        <div>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '15px'
          }}>
            <h2>
              {getProjectDisplayName(selectedProject)}
            </h2>
            <div>
              <button
                onClick={() => setShowTranscript(false)}
                style={{
                  backgroundColor: '#f1f1f1',
                  color: '#333',
                  padding: '8px 15px',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  marginRight: '10px'
                }}
              >
                Back to List
              </button>
              
              <button
                onClick={copyTranscript}
                style={{
                  backgroundColor: '#2196F3',
                  color: 'white',
                  padding: '8px 15px',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  marginRight: '10px'
                }}
              >
                Copy
              </button>
              
              <button
                onClick={() => downloadTranscript(selectedProject.id)}
                style={{
                  backgroundColor: '#4CAF50',
                  color: 'white',
                  padding: '8px 15px',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Download
              </button>
            </div>
          </div>
          
          {selectedProject.url && (
            <div style={{ marginBottom: '15px' }}>
              <p>Source: <a href={selectedProject.url} target="_blank" rel="noopener noreferrer">{selectedProject.url}</a></p>
            </div>
          )}
          
          <div style={{
            backgroundColor: 'white',
            border: '1px solid #ddd',
            borderRadius: '4px',
            padding: '15px',
            maxHeight: '500px',
            overflowY: 'auto',
            whiteSpace: 'pre-wrap',
            fontFamily: 'monospace',
            fontSize: '14px',
            lineHeight: '1.6'
          }}>
            {transcript || 'No transcript content available.'}
          </div>
        </div>
      ) : (
        <div>
          <h2>Available Projects</h2>
          <div style={{ 
            backgroundColor: 'white',
            borderRadius: '4px',
            overflow: 'hidden',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
          }}>
            <table style={{ 
              width: '100%',
              borderCollapse: 'collapse'
            }}>
              <thead>
                <tr style={{ backgroundColor: '#f5f5f5' }}>
                  <th style={{ padding: '12px 15px', textAlign: 'left' }}>Title</th>
                  <th style={{ padding: '12px 15px', textAlign: 'left' }}>Date</th>
                  <th style={{ padding: '12px 15px', textAlign: 'center' }}>Files</th>
                  <th style={{ padding: '12px 15px', textAlign: 'center' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {projects.map((project, index) => (
                  <tr 
                    key={project.id}
                    style={{ 
                      borderTop: '1px solid #eee',
                      backgroundColor: index % 2 === 0 ? 'white' : '#fafafa'
                    }}
                  >
                    <td style={{ padding: '12px 15px' }}>
                      <div style={{ fontWeight: 'bold' }}>{getProjectDisplayName(project)}</div>
                      {project.url && (
                        <div style={{ fontSize: '12px', color: '#777', marginTop: '5px' }}>
                          <a 
                            href={project.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            style={{ color: '#2196F3' }}
                          >
                            {formatYoutubeUrl(project.url)}
                          </a>
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '12px 15px' }}>
                      {formatDate(project.date)}
                    </td>
                    <td style={{ padding: '12px 15px', textAlign: 'center' }}>
                      <div>
                        {project.hasTranscript && (
                          <span style={{ 
                            backgroundColor: '#e8f5e9', 
                            color: '#2e7d32',
                            padding: '3px 8px',
                            borderRadius: '12px',
                            fontSize: '12px',
                            fontWeight: 'bold',
                            marginRight: '5px',
                            display: 'inline-block',
                            marginBottom: '5px'
                          }}>
                            Transcript
                          </span>
                        )}
                        
                        {project.audioFiles && project.audioFiles.length > 0 && (
                          <span style={{ 
                            backgroundColor: '#e3f2fd', 
                            color: '#1565c0',
                            padding: '3px 8px',
                            borderRadius: '12px',
                            fontSize: '12px',
                            fontWeight: 'bold',
                            display: 'inline-block'
                          }}>
                            Audio ({project.audioFiles.length})
                          </span>
                        )}
                        
                        {!project.hasTranscript && (!project.audioFiles || project.audioFiles.length === 0) && (
                          <span style={{ 
                            backgroundColor: '#ffebee', 
                            color: '#c62828',
                            padding: '3px 8px',
                            borderRadius: '12px',
                            fontSize: '12px',
                            fontWeight: 'bold'
                          }}>
                            No Files
                          </span>
                        )}
                      </div>
                    </td>
                    <td style={{ padding: '12px 15px', textAlign: 'center' }}>
                      <div style={{ marginBottom: '8px' }}>
                        {project.hasTranscript && (
                          <button
                            onClick={() => handleViewTranscript(project)}
                            style={{
                              backgroundColor: '#4CAF50',
                              color: 'white',
                              padding: '5px 10px',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              marginRight: '5px'
                            }}
                          >
                            View Transcript
                          </button>
                        )}
                        
                        <button
                          onClick={() => confirmDelete(project)}
                          style={{
                            backgroundColor: '#f44336',
                            color: 'white',
                            padding: '5px 10px',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer'
                          }}
                        >
                          Delete
                        </button>
                      </div>
                      
                      {project.audioFiles && project.audioFiles.length > 0 && (
                        <div style={{ marginTop: '8px' }}>
                          {project.audioFiles.map((audioFile) => (
                            <button
                              key={audioFile}
                              onClick={() => downloadAudio(project.id, audioFile)}
                              style={{
                                backgroundColor: '#2196F3',
                                color: 'white',
                                padding: '5px 10px',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                marginTop: '5px',
                                display: 'inline-block',
                                width: '100%',
                                maxWidth: '200px',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap'
                              }}
                              title={audioFile}
                            >
                              Download Audio
                            </button>
                          ))}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      
      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && projectToDelete && (
        <div style={{ 
          position: 'fixed', 
          top: 0, 
          left: 0, 
          right: 0, 
          bottom: 0, 
          backgroundColor: 'rgba(0,0,0,0.5)', 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{ 
            backgroundColor: 'white', 
            padding: '20px', 
            borderRadius: '8px',
            width: '400px',
            maxWidth: '90%'
          }}>
            <h3 style={{ marginTop: 0 }}>Delete Project</h3>
            <p>
              Are you sure you want to delete "{getProjectDisplayName(projectToDelete)}"? 
              This action cannot be undone and all associated files will be permanently removed.
            </p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '20px' }}>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                style={{
                  backgroundColor: '#f1f1f1',
                  color: '#333',
                  padding: '8px 15px',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  marginRight: '10px'
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteProject}
                style={{
                  backgroundColor: '#f44336',
                  color: 'white',
                  padding: '8px 15px',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DownloadsPage;