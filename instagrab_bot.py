from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import os
import instaloader
# import logging
import requests

# Configure logging
# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=logging.INFO
# )

# Function to check if a URL is accessible
def is_url_accessible(url):
    try:
        response = requests.head(url)
        return response.status_code == 200
    except requests.RequestException as e:
        # logging.error(f"Error checking URL accessibility: {e}")
        return False

# Function to fetch Instagram media (images and videos)
def fetch_instagram_media(url):
    try:
        loader = instaloader.Instaloader()
        post = instaloader.Post.from_shortcode(loader.context, url.split('/')[-2])
        
        media = []
        if post.is_video and is_url_accessible(post.video_url):
            media.append(InputMediaVideo(post.video_url))
        elif is_url_accessible(post.url):
            media.append(InputMediaPhoto(post.url))
        
        for node in post.get_sidecar_nodes():
            if node.is_video and is_url_accessible(node.video_url):
                media.append(InputMediaVideo(node.video_url))
            elif is_url_accessible(node.display_url):
                media.append(InputMediaPhoto(node.display_url))
        
        return media
    except Exception as e:
        # logging.error(f"Error fetching Instagram media: {e}")
        return None

# Start command
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Send me an Instagram post URL and I will fetch the media for you! 😙')

# Handle messages
async def handle_message(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    # Inform the user that the download is starting
    loading_message = await update.message.reply_text('Downloading media, please wait 🖐🏼')
    
    media = fetch_instagram_media(url)
    
    if media:
        try:
            await context.bot.send_media_group(chat_id=update.effective_chat.id, media=media)
        except Exception as e:
            # logging.error(f"Error sending media group: {e}")
            await update.message.reply_text('Failed to send media. Please try again later.')
        finally:
            # Delete the loading message after attempting to send the media
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=loading_message.message_id)
    else:
        await update.message.reply_text('Failed to fetch media from the provided Instagram post. Please check the URL and try again.')
        # Delete the loading message if fetching media fails
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=loading_message.message_id)

def main():
    token = os.getenv('INSTAGRAB_BOT_TOKEN')
    if not token:
        raise ValueError("No INSTAGRAB_BOT_TOKEN found. Please set the environment variable.")
    
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling()

if __name__ == '__main__':
    main()

