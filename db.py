import json
import os
from typing import Dict, List, Optional, Tuple, Any
import random
import logging
import sqlite3

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database file path
DB_FILE = "images.db"

# Default database structure
DEFAULT_DB = {
    "images": []  # List of image objects
}

def load_db() -> Dict:
    """Load database from file or create new one if not exists"""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    else:
        return DEFAULT_DB.copy()

def save_db(db: Dict) -> None:
    """Save database to file"""
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def init_db():
    """Initialize the database if it doesn't exist."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Create images table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            image_id TEXT PRIMARY KEY,
            number INTEGER,
            file_id TEXT,
            status TEXT DEFAULT 'open'
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

def add_image(image_id: str, number: int, file_id: str, status='open', metadata=None) -> bool:
    """Add an image to the database."""
    logger.info(f"Adding image: ID={image_id}, number={number}, file_id={file_id}")
    try:
        init_db()  # Make sure the database exists
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if image_id already exists
        cursor.execute("SELECT image_id FROM images WHERE image_id = ?", (image_id,))
        if cursor.fetchone():
            logger.warning(f"Image ID {image_id} already exists")
            conn.close()
            return False
        
        # Check if table has metadata column
        cursor.execute("PRAGMA table_info(images)")
        has_metadata = any(col[1] == 'metadata' for col in cursor.fetchall())
        
        # Add metadata column if it doesn't exist
        if not has_metadata:
            cursor.execute("ALTER TABLE images ADD COLUMN metadata TEXT")
            conn.commit()
            logger.info("Added metadata column to images table")
        
        # Insert new image with metadata
        cursor.execute(
            "INSERT INTO images (image_id, number, file_id, status, metadata) VALUES (?, ?, ?, ?, ?)",
            (image_id, number, file_id, status, metadata)
        )
        
        conn.commit()
        conn.close()
        logger.info(f"Added image {image_id} for group {number} with status '{status}'")
        return True
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error adding image: {e}")
        return False
    except Exception as e:
        logger.error(f"Error adding image: {e}")
        return False

def get_random_open_image() -> Optional[Dict]:
    """Get a random open image from the database."""
    try:
        init_db()  # Make sure the database exists
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if metadata column exists
        cursor.execute("PRAGMA table_info(images)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'metadata' in columns:
            cursor.execute("SELECT image_id, number, file_id, status, metadata FROM images WHERE status = 'open'")
        else:
            cursor.execute("SELECT image_id, number, file_id, status FROM images WHERE status = 'open'")
        
        rows = cursor.fetchall()
        
        if not rows:
            logger.info("No open images available")
            conn.close()
            return None
        
        # Pick a random image
        row = random.choice(rows)
        
        image = {
            'image_id': row[0],
            'number': row[1],
            'file_id': row[2],
            'status': row[3]
        }
        
        # Add metadata if available
        if 'metadata' in columns and len(row) > 4 and row[4]:
            try:
                image['metadata'] = json.loads(row[4])
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                logger.error(f"Error parsing metadata for image {row[0]}: {e}")
                image['metadata'] = {}
        
        conn.close()
        return image
    except Exception as e:
        logger.error(f"Error getting random open image: {e}")
        return None

def set_image_status(image_id: str, status: str) -> bool:
    """Set the status of an image."""
    logger.info(f"Setting image {image_id} status to '{status}'")
    try:
        init_db()  # Make sure the database exists
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if image exists
        cursor.execute("SELECT image_id FROM images WHERE image_id = ?", (image_id,))
        if not cursor.fetchone():
            logger.warning(f"Image ID {image_id} not found")
            conn.close()
            return False
        
        # Update status
        cursor.execute("UPDATE images SET status = ? WHERE image_id = ?", (status, image_id))
        
        conn.commit()
        conn.close()
        logger.info(f"Updated image {image_id} status to '{status}'")
        return True
    except Exception as e:
        logger.error(f"Error setting image status: {e}")
        return False

def get_all_images() -> List[Dict]:
    """Get all images from the database."""
    try:
        init_db()  # Make sure the database exists
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if metadata column exists
        cursor.execute("PRAGMA table_info(images)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'metadata' in columns:
            cursor.execute("SELECT image_id, number, file_id, status, metadata FROM images")
        else:
            cursor.execute("SELECT image_id, number, file_id, status FROM images")
        
        images = []
        for row in cursor.fetchall():
            image = {
                'image_id': row[0],
                'number': row[1],
                'file_id': row[2],
                'status': row[3]
            }
            
            # Add metadata if available
            if 'metadata' in columns and len(row) > 4 and row[4]:
                try:
                    image['metadata'] = json.loads(row[4])
                except:
                    image['metadata'] = {}
            
            images.append(image)
        
        conn.close()
        return images
    except Exception as e:
        logger.error(f"Error getting all images: {e}")
        return []

def get_image_by_id(image_id: str) -> Optional[Dict]:
    """Get an image by ID."""
    try:
        init_db()  # Make sure the database exists
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if metadata column exists
        cursor.execute("PRAGMA table_info(images)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'metadata' in columns:
            cursor.execute("SELECT image_id, number, file_id, status, metadata FROM images WHERE image_id = ?", (image_id,))
        else:
            cursor.execute("SELECT image_id, number, file_id, status FROM images WHERE image_id = ?", (image_id,))
        
        row = cursor.fetchone()
        
        if not row:
            logger.warning(f"Image ID {image_id} not found")
            conn.close()
            return None
        
        image = {
            'image_id': row[0],
            'number': row[1],
            'file_id': row[2],
            'status': row[3]
        }
        
        # Add metadata if available
        if 'metadata' in columns and len(row) > 4 and row[4]:
            try:
                image['metadata'] = json.loads(row[4])
                logger.info(f"Retrieved metadata for image {image_id}: {image['metadata']}")
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                logger.error(f"Error parsing metadata for image {row[0]}: {e}")
                image['metadata'] = {}
        
        conn.close()
        return image
    except Exception as e:
        logger.error(f"Error getting image by ID: {e}")
        return None

def count_images_by_status() -> Tuple[int, int]:
    """Count the number of open and closed images."""
    try:
        init_db()  # Make sure the database exists
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM images WHERE status = 'open'")
        open_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM images WHERE status = 'closed'")
        closed_count = cursor.fetchone()[0]
        
        conn.close()
        return open_count, closed_count
    except Exception as e:
        logger.error(f"Error counting images by status: {e}")
        return 0, 0

def get_image_path(image_id: str) -> Optional[str]:
    """Get the path to an image file (for backward compatibility)."""
    try:
        image = get_image_by_id(image_id)
        if not image:
            return None
        
        # This is a placeholder since we're now using file_id
        # In a real system with local files, this would return the actual file path
        return f"images/{image_id}.jpg"
    except Exception as e:
        logger.error(f"Error getting image path: {e}")
        return None

def reset_all_image_statuses() -> bool:
    """Reset all image statuses to open."""
    try:
        init_db()  # Make sure the database exists
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("UPDATE images SET status = 'open'")
        
        conn.commit()
        conn.close()
        logger.info("Reset all image statuses to 'open'")
        return True
    except Exception as e:
        logger.error(f"Error resetting image statuses: {e}")
        return False

def clear_all_images():
    """Delete all images from the database."""
    try:
        init_db()  # Make sure the database exists
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM images")
        
        conn.commit()
        conn.close()
        logger.info("All images deleted from database")
        return True
    except Exception as e:
        logger.error(f"Database error in clear_all_images: {e}")
        return False

def update_image_metadata(image_id: str, metadata: str) -> bool:
    """Update an image's metadata."""
    logger.info(f"Updating metadata for image {image_id}: {metadata}")
    try:
        init_db()  # Make sure the database exists
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if image exists
        cursor.execute("SELECT image_id FROM images WHERE image_id = ?", (image_id,))
        if not cursor.fetchone():
            logger.warning(f"Image ID {image_id} not found")
            conn.close()
            return False
        
        # Check if metadata column exists
        cursor.execute("PRAGMA table_info(images)")
        has_metadata = any(col[1] == 'metadata' for col in cursor.fetchall())
        
        # Add metadata column if it doesn't exist
        if not has_metadata:
            cursor.execute("ALTER TABLE images ADD COLUMN metadata TEXT")
            conn.commit()
            logger.info("Added metadata column to images table")
        
        # Update metadata
        cursor.execute("UPDATE images SET metadata = ? WHERE image_id = ?", (metadata, image_id))
        
        conn.commit()
        conn.close()
        logger.info(f"Updated metadata for image {image_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating image metadata: {e}")
        return False

def get_random_open_image_by_group_b(group_b_id: int) -> Optional[Dict]:
    """Get a random open image that belongs to a specific Group B."""
    try:
        init_db()  # Make sure the database exists
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if metadata column exists
        cursor.execute("PRAGMA table_info(images)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'metadata' not in columns:
            logger.warning("Cannot filter by group_b_id as metadata column does not exist")
            conn.close()
            return get_random_open_image()  # Fall back to regular random selection
        
        # Get all open images first
        cursor.execute("SELECT image_id, number, file_id, status, metadata FROM images WHERE status = 'open'")
        
        rows = cursor.fetchall()
        
        if not rows:
            logger.info("No open images available")
            conn.close()
            return None
        
        # Filter images by Group B ID
        filtered_rows = []
        for row in rows:
            if row[4]:  # If metadata exists
                try:
                    metadata = json.loads(row[4])
                    if isinstance(metadata, dict) and 'source_group_b_id' in metadata:
                        if int(metadata['source_group_b_id']) == int(group_b_id):
                            filtered_rows.append(row)
                except (ValueError, TypeError, json.JSONDecodeError) as e:
                    logger.error(f"Error processing metadata for image {row[0]}: {e}")
        
        # If we found matching images, pick a random one
        if filtered_rows:
            logger.info(f"Found {len(filtered_rows)} open images for Group B ID {group_b_id}")
            row = random.choice(filtered_rows)
            
            image = {
                'image_id': row[0],
                'number': row[1],
                'file_id': row[2],
                'status': row[3]
            }
            
            if row[4]:
                try:
                    image['metadata'] = json.loads(row[4])
                except (ValueError, TypeError, json.JSONDecodeError) as e:
                    logger.error(f"Error parsing metadata for image {row[0]}: {e}")
                    image['metadata'] = {}
            
            conn.close()
            return image
        else:
            # If no matching images, fall back to any open image
            logger.info(f"No open images found for Group B ID {group_b_id}, falling back to any open image")
            conn.close()
            return get_random_open_image() 
    except Exception as e:
        logger.error(f"Error in get_random_open_image_by_group_b: {e}")
        return get_random_open_image()  # Fall back to any open image on error 

def clear_images_by_group_b(group_b_id: int):
    """Delete images associated with a specific Group B from the database."""
    try:
        init_db()  # Make sure the database exists
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if metadata column exists
        cursor.execute("PRAGMA table_info(images)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'metadata' not in columns:
            logger.warning("Cannot filter by group_b_id as metadata column does not exist")
            conn.close()
            return False
        
        # First count total images
        cursor.execute("SELECT COUNT(*) FROM images")
        total_count = cursor.fetchone()[0]
        logger.info(f"Total images in database before deletion: {total_count}")
        
        # Get all images first
        cursor.execute("SELECT image_id, metadata FROM images")
        rows = cursor.fetchall()
        
        if not rows:
            logger.info("No images available to clear")
            conn.close()
            return True
        
        # Find images to delete by checking their metadata
        images_to_delete = []
        for row in rows:
            image_id, metadata_str = row
            if metadata_str:
                try:
                    metadata = json.loads(metadata_str)
                    if isinstance(metadata, dict) and 'source_group_b_id' in metadata:
                        source_id = int(metadata['source_group_b_id'])
                        target_id = int(group_b_id)
                        logger.info(f"Comparing metadata Group B ID {source_id} with target {target_id}")
                        if source_id == target_id:
                            images_to_delete.append(image_id)
                            logger.info(f"Will delete image {image_id}")
                except (ValueError, TypeError, json.JSONDecodeError) as e:
                    logger.error(f"Error processing metadata for image {image_id}: {e}")
            else:
                logger.info(f"Image {image_id} has no metadata")
        
        # Delete the matching images
        if images_to_delete:
            placeholders = ', '.join(['?'] * len(images_to_delete))
            cursor.execute(f"DELETE FROM images WHERE image_id IN ({placeholders})", images_to_delete)
            conn.commit()
            
            # Verify deletion by counting remaining images
            cursor.execute("SELECT COUNT(*) FROM images")
            remaining_count = cursor.fetchone()[0]
            deleted_count = total_count - remaining_count
            
            logger.info(f"Database had {total_count} images, deleted {deleted_count}, {remaining_count} remaining")
            logger.info(f"Deleted {len(images_to_delete)} images for Group B ID {group_b_id}")
        else:
            logger.info(f"No images found for Group B ID {group_b_id}")
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database error in clear_images_by_group_b: {e}")
        return False 

def delete_image_by_number(number: int, group_b_id: int) -> bool:
    """Delete a specific image by its number from the database."""
    try:
        init_db()  # Make sure the database exists
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if metadata column exists
        cursor.execute("PRAGMA table_info(images)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'metadata' not in columns:
            logger.warning("Cannot filter by group_b_id as metadata column does not exist")
            conn.close()
            return False
        
        # Get all images matching this number
        cursor.execute("SELECT image_id, metadata FROM images WHERE number = ?", (number,))
        rows = cursor.fetchall()
        
        if not rows:
            logger.info(f"No images found with number {number}")
            conn.close()
            return False
        
        # Find images to delete by checking their metadata for matching Group B ID
        images_to_delete = []
        for row in rows:
            image_id, metadata_str = row
            if metadata_str:
                try:
                    metadata = json.loads(metadata_str)
                    if isinstance(metadata, dict) and 'source_group_b_id' in metadata:
                        source_id = int(metadata['source_group_b_id'])
                        target_id = int(group_b_id)
                        logger.info(f"Comparing metadata Group B ID {source_id} with target {target_id}")
                        if source_id == target_id:
                            images_to_delete.append(image_id)
                            logger.info(f"Will delete image {image_id} with number {number}")
                except (ValueError, TypeError, json.JSONDecodeError) as e:
                    logger.error(f"Error processing metadata for image {image_id}: {e}")
            else:
                logger.info(f"Image {image_id} has no metadata")
        
        # Delete the matching images
        if images_to_delete:
            placeholders = ', '.join(['?'] * len(images_to_delete))
            cursor.execute(f"DELETE FROM images WHERE image_id IN ({placeholders})", images_to_delete)
            conn.commit()
            
            logger.info(f"Deleted {len(images_to_delete)} images with number {number} for Group B ID {group_b_id}")
            conn.close()
            return True
        else:
            logger.info(f"No matching images found with number {number} for Group B ID {group_b_id}")
            conn.close()
            return False
    except Exception as e:
        logger.error(f"Database error in delete_image_by_number: {e}")
        return False 

def get_next_open_image_ascending() -> Optional[Dict]:
    """Get the next open image in ascending order by number."""
    try:
        init_db()  # Make sure the database exists
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if metadata column exists
        cursor.execute("PRAGMA table_info(images)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'metadata' in columns:
            cursor.execute("SELECT image_id, number, file_id, status, metadata FROM images WHERE status = 'open' ORDER BY number ASC")
        else:
            cursor.execute("SELECT image_id, number, file_id, status FROM images WHERE status = 'open' ORDER BY number ASC")
        
        rows = cursor.fetchall()
        
        if not rows:
            logger.info("No open images available")
            conn.close()
            return None
        
        # Get the first image (lowest number)
        row = rows[0]
        
        image = {
            'image_id': row[0],
            'number': row[1],
            'file_id': row[2],
            'status': row[3]
        }
        
        # Add metadata if available
        if 'metadata' in columns and len(row) > 4 and row[4]:
            try:
                image['metadata'] = json.loads(row[4])
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                logger.error(f"Error parsing metadata for image {row[0]}: {e}")
                image['metadata'] = {}
        
        conn.close()
        return image
    except Exception as e:
        logger.error(f"Error getting next open image in ascending order: {e}")
        return None 

def get_next_open_image_ascending_with_percentage(group_b_percentages: Dict = None) -> Optional[Dict]:
    """Get the next open image in ascending order by number, considering Group B percentages as priority."""
    try:
        init_db()  # Make sure the database exists
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if metadata column exists
        cursor.execute("PRAGMA table_info(images)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'metadata' in columns:
            cursor.execute("SELECT image_id, number, file_id, status, metadata FROM images WHERE status = 'open' ORDER BY number ASC")
        else:
            cursor.execute("SELECT image_id, number, file_id, status FROM images WHERE status = 'open' ORDER BY number ASC")
        
        rows = cursor.fetchall()
        
        if not rows:
            logger.info("No open images available")
            conn.close()
            return None
        
        # If no percentage settings, return first image
        if not group_b_percentages:
            row = rows[0]
            image = {
                'image_id': row[0],
                'number': row[1],
                'file_id': row[2],
                'status': row[3]
            }
            
            # Add metadata if available
            if 'metadata' in columns and len(row) > 4 and row[4]:
                try:
                    image['metadata'] = json.loads(row[4])
                except (ValueError, TypeError, json.JSONDecodeError) as e:
                    logger.error(f"Error parsing metadata for image {row[0]}: {e}")
                    image['metadata'] = {}
            
            conn.close()
            return image
        
        # PRIORITY SYSTEM: First, try to find images from 100% Group Bs (highest priority)
        priority_images = []
        high_percentage_images = []
        normal_images = []
        
        for row in rows:
            image = {
                'image_id': row[0],
                'number': row[1],
                'file_id': row[2],
                'status': row[3]
            }
            
            # Add metadata if available
            if 'metadata' in columns and len(row) > 4 and row[4]:
                try:
                    image['metadata'] = json.loads(row[4])
                except (ValueError, TypeError, json.JSONDecodeError) as e:
                    logger.error(f"Error parsing metadata for image {row[0]}: {e}")
                    image['metadata'] = {}
            else:
                image['metadata'] = {}
            
            # Check if this image has Group B metadata
            metadata = image.get('metadata', {})
            if isinstance(metadata, dict) and 'source_group_b_id' in metadata:
                try:
                    source_group_b_id = int(metadata['source_group_b_id'])
                    
                    # Check percentage setting for this Group B
                    if source_group_b_id in group_b_percentages:
                        percentage = group_b_percentages[source_group_b_id]
                        
                        if percentage == 100:
                            # 100% = Highest priority - these should be sent first
                            priority_images.append(image)
                            logger.info(f"Image {image['image_id']} from Group B {source_group_b_id} has 100% priority")
                        elif percentage >= 50:
                            # High percentage images
                            high_percentage_images.append((image, percentage))
                        else:
                            # Lower percentage images
                            normal_images.append((image, percentage))
                    else:
                        # No specific percentage setting, treat as normal
                        normal_images.append((image, 100))  # Default 100% if not specified
                        
                except (ValueError, TypeError) as e:
                    logger.error(f"Error processing metadata for image {row[0]}: {e}")
                    normal_images.append((image, 100))  # Default if error
            else:
                # No metadata or no Group B ID, treat as normal
                normal_images.append((image, 100))  # Default 100%
        
        # Return images by priority:
        # 1. First, return any 100% priority images (in ascending order)
        if priority_images:
            selected_image = priority_images[0]  # Already sorted by number ASC
            logger.info(f"Selected priority image: {selected_image['image_id']} (100% priority)")
            conn.close()
            return selected_image
        
        # 2. Then try high percentage images (with chance)
        if high_percentage_images:
            import random
            for image, percentage in high_percentage_images:
                random_chance = random.randint(1, 100)
                logger.info(f"Image {image['image_id']} has {percentage}% chance, rolled {random_chance}")
                if random_chance <= percentage:
                    logger.info(f"Selected high percentage image: {image['image_id']}")
                    conn.close()
                    return image
        
        # 3. Finally try normal/lower percentage images
        if normal_images:
            import random
            for image, percentage in normal_images:
                random_chance = random.randint(1, 100)
                logger.info(f"Image {image['image_id']} has {percentage}% chance, rolled {random_chance}")
                if random_chance <= percentage:
                    logger.info(f"Selected normal image: {image['image_id']}")
                    conn.close()
                    return image
        
        # If we get here, all images were skipped due to percentage, return None
        logger.info("All open images were skipped due to percentage restrictions")
        conn.close()
        return None
        
    except Exception as e:
        logger.error(f"Error getting next open image with percentage: {e}")
        return None 

def get_next_image_in_queue() -> Optional[Dict]:
    """Get the next image in queue order (setup/creation order), cycling through all images, but only consider OPEN images."""
    try:
        init_db()  # Make sure the database exists
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Add queue_position column if it doesn't exist
        cursor.execute("PRAGMA table_info(images)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'queue_position' not in columns:
            cursor.execute("ALTER TABLE images ADD COLUMN queue_position INTEGER DEFAULT 0")
            conn.commit()
            logger.info("Added queue_position column to images table")
        
        # Get all images ordered by rowid (creation order) - ALL images for position tracking
        if 'metadata' in columns:
            cursor.execute("SELECT rowid, image_id, number, file_id, status, metadata, queue_position FROM images ORDER BY rowid ASC")
        else:
            cursor.execute("SELECT rowid, image_id, number, file_id, status, queue_position FROM images ORDER BY rowid ASC")
        
        all_rows = cursor.fetchall()
        
        if not all_rows:
            logger.info("No images available in queue")
            conn.close()
            return None
        
        # Filter to only get OPEN images for selection
        open_rows = [row for row in all_rows if row[4] == 'open']  # status is at index 4
        
        if not open_rows:
            logger.info("No open images available in queue")
            conn.close()
            return None
        
        # Find the last sent image (highest queue_position) among ALL images
        max_position = max(row[-1] or 0 for row in all_rows)  # queue_position is last column
        
        # Find next OPEN image in queue after the last sent position
        next_image = None
        
        if max_position == 0:
            # No images sent yet, start with first open image
            next_image = open_rows[0]
            logger.info("Starting queue from first open image")
        else:
            # Find the image with max_position
            last_sent_rowid = None
            for row in all_rows:
                if (row[-1] or 0) == max_position:
                    last_sent_rowid = row[0]  # rowid
                    break
            
            if last_sent_rowid is not None:
                # Find the next OPEN image after the last sent image
                for row in open_rows:
                    if row[0] > last_sent_rowid:  # rowid comparison
                        next_image = row
                        logger.info(f"Found next open image after rowid {last_sent_rowid}")
                        break
                
                # If no open image found after last sent, cycle back to first open image
                if not next_image and open_rows:
                    next_image = open_rows[0]
                    logger.info("Cycling back to first open image")
            
            # Fallback if we couldn't find the last sent image
            if not next_image and open_rows:
                next_image = open_rows[0]
                logger.info("Fallback: using first open image")
        
        if not next_image:
            logger.info("No suitable next image found")
            conn.close()
            return None
        
        # Build image dict
        image = {
            'image_id': next_image[1],
            'number': next_image[2],
            'file_id': next_image[3],
            'status': next_image[4],
            'rowid': next_image[0]
        }
        
        # Add metadata if available
        if 'metadata' in columns and len(next_image) > 5 and next_image[5]:
            try:
                image['metadata'] = json.loads(next_image[5])
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                logger.error(f"Error parsing metadata for image {next_image[1]}: {e}")
                image['metadata'] = {}
        
        # Update queue position for this image
        new_position = max_position + 1
        cursor.execute("UPDATE images SET queue_position = ? WHERE image_id = ?", (new_position, image['image_id']))
        conn.commit()
        
        logger.info(f"Selected next OPEN image in queue: {image['image_id']} (position {new_position}, status: {image['status']})")
        conn.close()
        return image
        
    except Exception as e:
        logger.error(f"Error getting next image in queue: {e}")
        return None

def get_next_image_in_queue_with_percentage(group_b_percentages: Dict = None) -> Optional[Dict]:
    """Get the next image in queue order with Group B percentage filtering."""
    try:
        # Get the next image in queue
        image = get_next_image_in_queue()
        
        if not image or not group_b_percentages:
            return image
        
        # Check percentage restrictions
        metadata = image.get('metadata', {})
        if isinstance(metadata, dict) and 'source_group_b_id' in metadata:
            try:
                source_group_b_id = int(metadata['source_group_b_id'])
                
                if source_group_b_id in group_b_percentages:
                    percentage = group_b_percentages[source_group_b_id]
                    
                    # Roll for percentage chance
                    import random
                    random_chance = random.randint(1, 100)
                    logger.info(f"Image {image['image_id']} from Group B {source_group_b_id} has {percentage}% chance, rolled {random_chance}")
                    
                    if random_chance <= percentage:
                        logger.info(f"Image {image['image_id']} passed percentage check")
                        return image
                    else:
                        logger.info(f"Image {image['image_id']} failed percentage check, trying next image")
                        # Recursively try next image (but limit recursion)
                        return get_next_image_in_queue_with_percentage(group_b_percentages)
                
            except (ValueError, TypeError) as e:
                logger.error(f"Error processing metadata for image {image['image_id']}: {e}")
        
        # No percentage restriction or error, return image
        return image
        
    except Exception as e:
        logger.error(f"Error getting next image in queue with percentage: {e}")
        return None 

def reset_queue_positions() -> bool:
    """Reset all queue positions to start fresh."""
    try:
        init_db()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if queue_position column exists
        cursor.execute("PRAGMA table_info(images)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'queue_position' in columns:
            cursor.execute("UPDATE images SET queue_position = 0")
            conn.commit()
            logger.info("Reset all queue positions to 0")
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error resetting queue positions: {e}")
        return False

def get_queue_status() -> Dict[str, Any]:
    """Get current queue status for debugging."""
    try:
        init_db()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if queue_position column exists
        cursor.execute("PRAGMA table_info(images)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'queue_position' not in columns:
            return {"error": "Queue system not initialized"}
        
        # Get all images with queue positions
        cursor.execute("SELECT image_id, number, status, queue_position FROM images ORDER BY rowid ASC")
        rows = cursor.fetchall()
        
        if not rows:
            return {"error": "No images in queue"}
        
        # Separate open and closed images
        open_images = [row for row in rows if row[2] == 'open']
        closed_images = [row for row in rows if row[2] == 'closed']
        
        max_position = max(row[3] or 0 for row in rows)
        
        # Find current position in queue
        current_image = None
        for row in rows:
            if (row[3] or 0) == max_position:
                current_image = {"id": row[0], "number": row[1], "status": row[2], "position": row[3]}
                break
        
        # Find next OPEN image
        next_image = None
        if current_image:
            current_rowid = None
            cursor.execute("SELECT rowid FROM images WHERE image_id = ?", (current_image["id"],))
            result = cursor.fetchone()
            if result:
                current_rowid = result[0]
                
                # Find next OPEN image after current
                cursor.execute("SELECT image_id, number FROM images WHERE rowid > ? AND status = 'open' ORDER BY rowid ASC LIMIT 1", (current_rowid,))
                result = cursor.fetchone()
                if result:
                    next_image = {"id": result[0], "number": result[1], "status": "open"}
                else:
                    # Cycle back to first OPEN image
                    cursor.execute("SELECT image_id, number FROM images WHERE status = 'open' ORDER BY rowid ASC LIMIT 1")
                    result = cursor.fetchone()
                    if result:
                        next_image = {"id": result[0], "number": result[1], "status": "open"}
        
        conn.close()
        
        return {
            "total_images": len(rows),
            "open_images": len(open_images),
            "closed_images": len(closed_images),
            "max_position": max_position,
            "current_image": current_image,
            "next_image": next_image,
            "queue_order": [{"id": row[0], "number": row[1], "status": row[2], "position": row[3] or 0} for row in rows]
        }
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        return {"error": str(e)} 
