class ChannelService: #crear ChannelServicePort e implementarlo aqui

    async def update_channel_prompt(self, channel_id, selected_prompt_id=None, selected_master_prompt_id=None):
        
        # Business rule: mutually exclusive
        if selected_prompt_id and selected_master_prompt_id:
            raise ValueError("A channel cannot select both a user prompt and a master prompt.")

        # Optional: require at least one
        if not selected_prompt_id and not selected_master_prompt_id:
            raise ValueError("A channel must select either a user prompt or a master prompt.")

        # Persist changes
        await self.channel_repo.update_by_id(
            channel_id,
            {
                "selectedPromptId": selected_prompt_id,
                "selectedMasterPromptId": selected_master_prompt_id,
                "updatedAt": datetime.utcnow()
            }
        )
